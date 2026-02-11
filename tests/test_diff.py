"""Tests for diff filtering functionality."""
import subprocess
import pytest
from unittest.mock import patch, MagicMock

from lazypr import (
    get_diff,
    parse_diff_lines,
    filter_large_files,
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
        with patch("src.lazypr.diff.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=diff_output
            )
            result = get_diff("main")
            assert result == diff_output

    def test_raises_error_when_base_branch_missing(self):
        """Should raise DiffError when base branch doesn't exist."""
        with patch("src.lazypr.diff.subprocess.run") as mock_run:
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
