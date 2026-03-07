"""Tests for diff filtering functionality."""
import subprocess
import pytest
from unittest.mock import patch, MagicMock, call

from lazypr.diff import (
    get_diff,
    get_diff_remote,
    parse_diff_lines,
    filter_large_files,
    rebuild_diff_with_files,
    DiffError,
)


class TestGetDiff:
    """Tests for get_diff() function."""

    def test_returns_diff_string(self):
        """Should return diff output as string."""
        diff_output = """diff --git a/file.py b/file.py
index 123..456 100644
--- a/file.py
+++ b/file.py
@@ -1,5 +1,5 @@
 def hello():
-    print("old")
+    print("new")
"""
        with patch("lazypr.diff.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=diff_output
            )
            result = get_diff("main")
            assert result == diff_output

    def test_raises_error_when_base_branch_missing(self):
        """Should raise DiffError when base branch doesn't exist."""
        with patch("lazypr.diff.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(128, "git")
            with pytest.raises(DiffError):
                get_diff("nonexistent-branch")


class TestParseDiffLines:
    """Tests for parse_diff_lines() function."""

    def test_parses_single_file_diff(self):
        """Should correctly count lines per file."""
        diff = """diff --git a/file.py b/file.py
index 123..456 100644
--- a/file.py
+++ b/file.py
@@ -1,5 +1,5 @@
 def hello():
-    print("old")
+    print("new")
"""
        result = parse_diff_lines(diff)
        assert result == {"file.py": 8}

    def test_parses_multiple_files(self):
        """Should count lines for multiple files."""
        diff = """diff --git a/file1.py b/file1.py
index 123..456 100644
--- a/file1.py
+++ b/file1.py
@@ -1,2 +1,2 @@
 line1
-line2
+line2_modified

diff --git a/file2.py b/file2.py
index 789..abc 100644
--- a/file2.py
+++ b/file2.py
@@ -1,3 +1,3 @@
 a
-b
+c
 d
"""
        result = parse_diff_lines(diff)
        assert result == {"file1.py": 8, "file2.py": 9}

    def test_handles_binary_files(self):
        """Should skip binary files in diff."""
        diff = """diff --git a/image.png b/image.png
Binary files differ

diff --git a/text.txt b/text.txt
index 123..456 100644
--- a/text.txt
+++ b/text.txt
@@ -1 +1 @@
-old
+new
"""
        result = parse_diff_lines(diff)
        assert "image.png" not in result
        assert "text.txt" in result


class TestFilterLargeFiles:
    """Tests for filter_large_files() function."""

    def test_removes_files_exceeding_threshold(self):
        """Should remove files with diff lines > threshold."""
        diff = """diff --git a/small.py b/small.py
index 123..456 100644
--- a/small.py
+++ b/small.py
@@ -1 +1 @@
-old
+new

diff --git a/large.py b/large.py
index 789..abc 100644
--- a/large.py
+++ b/large.py
@@ -1,1000 +1,1000 @@
"""
        result = filter_large_files(diff, max_lines=10)
        assert "small.py" in result
        assert "large.py" not in result

    def test_keeps_all_files_when_under_threshold(self):
        """Should keep all files when under threshold."""
        diff = """diff --git a/file.py b/file.py
index 123..456 100644
--- a/file.py
+++ b/file.py
@@ -1 +1 @@
-old
+new
"""
        result = filter_large_files(diff, max_lines=100)
        assert "file.py" in result

    def test_returns_empty_string_when_all_files_filtered(self):
        """Should return empty string when all files exceed threshold."""
        diff = """diff --git a/huge.py b/huge.py
index 123..456 100644
--- a/huge.py
+++ b/huge.py
@@ -1,2000 +1,2000 @@
"""
        result = filter_large_files(diff, max_lines=100)
        assert result == ""


class TestGetDiffRemote:
    """Tests for get_diff_remote() function."""

    def test_returns_diff_from_remote_branch(self):
        """Should return diff output comparing remote branch to HEAD."""
        diff_output = """diff --git a/file.py b/file.py
index 123..456 100644
--- a/file.py
+++ b/file.py
@@ -1,5 +1,5 @@
 def hello():
-    print("old")
+    print("new")
"""
        branch_list = MagicMock(returncode=0, stdout="  origin/main\n")
        fetch_result = MagicMock(returncode=0, stdout="")
        diff_result = MagicMock(returncode=0, stdout=diff_output)
        with patch("lazypr.diff.subprocess.run", side_effect=[branch_list, fetch_result, diff_result]) as mock_run:
            result = get_diff_remote("main")
            # Third call must be the diff
            diff_call = mock_run.call_args_list[2]
            assert diff_call == call(
                ["git", "diff", "origin/main...HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            assert result == diff_output

    def test_uses_custom_remote(self):
        """Should allow custom remote name."""
        branch_list = MagicMock(returncode=0, stdout="  upstream/main\n")
        fetch_result = MagicMock(returncode=0, stdout="")
        diff_result = MagicMock(returncode=0, stdout="diff output")
        with patch("lazypr.diff.subprocess.run", side_effect=[branch_list, fetch_result, diff_result]) as mock_run:
            result = get_diff_remote("main", remote="upstream")
            diff_call = mock_run.call_args_list[2]
            assert diff_call == call(
                ["git", "diff", "upstream/main...HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            assert result == "diff output"

    def test_raises_error_when_remote_branch_missing(self):
        """Should raise DiffError when no remote branch exists for base."""
        branch_list = MagicMock(returncode=0, stdout="  origin/other\n")
        with patch("lazypr.diff.subprocess.run", side_effect=[branch_list, subprocess.CalledProcessError(128, "git")]):
            with pytest.raises(DiffError) as exc_info:
                get_diff_remote("nonexistent-branch")
            assert "nonexistent-branch" in str(exc_info.value)

    def test_fetches_remote_before_diffing(self):
        """Should fetch from remote before running diff to get up-to-date tracking ref."""
        diff_output = "diff --git a/file.py b/file.py\n"
        branch_list = MagicMock(returncode=0, stdout="  origin/main\n")
        fetch_result = MagicMock(returncode=0, stdout="")
        diff_result = MagicMock(returncode=0, stdout=diff_output)
        with patch("lazypr.diff.subprocess.run", side_effect=[branch_list, fetch_result, diff_result]) as mock_run:
            result = get_diff_remote("main")
            # Second call must be the fetch
            fetch_call = mock_run.call_args_list[1]
            assert fetch_call == call(
                ["git", "fetch", "origin", "main"],
                capture_output=True,
                text=True,
                check=True,
            )
            assert result == diff_output

    def test_fetch_failure_is_ignored(self):
        """Should proceed with cached tracking ref when fetch fails (e.g. offline)."""
        diff_output = "diff --git a/file.py b/file.py\n"
        branch_list = MagicMock(returncode=0, stdout="  origin/main\n")
        diff_result = MagicMock(returncode=0, stdout=diff_output)
        with patch("lazypr.diff.subprocess.run", side_effect=[
            branch_list,
            subprocess.CalledProcessError(1, "git fetch"),
            diff_result,
        ]):
            result = get_diff_remote("main")
            assert result == diff_output

    def test_local_fallback_does_not_fetch(self):
        """Should not attempt a fetch when falling back to local branch ref."""
        diff_output = "diff --git a/file.py b/file.py\n"
        # No remote branches available → falls back to local 'main'
        branch_list = MagicMock(returncode=0, stdout="")
        diff_result = MagicMock(returncode=0, stdout=diff_output)
        with patch("lazypr.diff.subprocess.run", side_effect=[branch_list, diff_result]) as mock_run:
            result = get_diff_remote("main")
            # Only two calls: branch_list + diff (no fetch for local ref)
            assert mock_run.call_count == 2
            assert result == diff_output


class TestRebuildDiffWithFiles:
    """Tests for rebuild_diff_with_files() function."""

    def test_rebuilds_diff_with_allowed_files(self):
        """Should include only files in the allowed list."""
        diff = """diff --git a/file1.py b/file1.py
index 123..456 100644
--- a/file1.py
+++ b/file1.py
@@ -1 +1 @@
-old1
+new1

diff --git a/file2.py b/file2.py
index 789..abc 100644
--- a/file2.py
+++ b/file2.py
@@ -1 +1 @@
-old2
+new2
"""
        result = rebuild_diff_with_files(diff, ["file1.py"])
        assert "file1.py" in result
        assert "file2.py" not in result
        assert "new1" in result

    def test_returns_empty_when_no_files_allowed(self):
        """Should return empty string when no files match."""
        diff = """diff --git a/file1.py b/file1.py
index 123..456 100644
--- a/file1.py
+++ b/file1.py
@@ -1 +1 @@
-old
+new
"""
        result = rebuild_diff_with_files(diff, ["other.py"])
        assert result == ""

    def test_returns_empty_for_empty_diff(self):
        """Should return empty string for empty diff input."""
        result = rebuild_diff_with_files("", ["file.py"])
        assert result == ""
