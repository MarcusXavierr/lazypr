"""Tests for .lazyprignore pattern matching."""
import pytest
from unittest.mock import patch, mock_open

from lazypr import (
    load_ignore_patterns,
    apply_ignore_patterns,
    matches_pattern,
)


class TestLoadIgnorePatterns:
    """Tests for load_ignore_patterns() function."""

    def test_loads_patterns_from_file(self):
        """Should load patterns from .lazyprignore file."""
        with patch("src.lazypr.ignore.Path.exists") as mock_exists:
            mock_exists.return_value = True
            with patch("builtins.open", mock_open(read_data="*.log\n__pycache__/\n*.tmp\n")):
                patterns = load_ignore_patterns()
                assert "*.log" in patterns
                assert "__pycache__/" in patterns
                assert "*.tmp" in patterns

    def test_returns_empty_list_when_file_missing(self):
        """Should return empty list when .lazyprignore doesn't exist."""
        with patch("src.lazypr.ignore.Path.exists") as mock_exists:
            mock_exists.return_value = False
            patterns = load_ignore_patterns()
            assert patterns == []

    def test_skips_comments_and_empty_lines(self):
        """Should ignore comment lines and empty lines."""
        content = """# This is a comment
*.log

# Another comment
__pycache__/
"""
        with patch("src.lazypr.ignore.Path.exists") as mock_exists:
            mock_exists.return_value = True
            with patch("builtins.open", mock_open(read_data=content)):
                patterns = load_ignore_patterns()
                assert "*.log" in patterns
                assert "__pycache__/" in patterns
                assert "# This is a comment" not in [p for p in patterns if p]
                assert "" not in [p for p in patterns if p]


class TestMatchesPattern:
    """Tests for matches_pattern() function."""

    @pytest.mark.parametrize("pattern,filepath,expected", [
        ("*.log", "debug.log", True),
        ("*.log", "debug.txt", False),
        ("__pycache__/", "__pycache__/file.pyc", True),
        ("__pycache__/", "src/__pycache__/file.pyc", True),
        ("temp/**", "temp/file.txt", True),
        ("temp/**", "temp/subdir/file.txt", True),
        ("*.pyc", "file.pyc", True),
        ("*.pyc", "file.py", False),
    ])
    def test_pattern_matching(self, pattern, filepath, expected):
        """Should correctly match glob patterns to file paths."""
        assert matches_pattern(pattern, filepath) == expected

    def test_negation_pattern(self):
        """Should handle negation patterns (!pattern)."""
        assert matches_pattern("!important.log", "debug.log") is False
        assert matches_pattern("!important.log", "important.log") is True


class TestApplyIgnorePatterns:
    """Tests for apply_ignore_patterns() function."""

    def test_filters_matching_files(self):
        """Should remove files matching ignore patterns."""
        files = ["app.py", "debug.log", "error.log", "main.py"]
        patterns = ["*.log"]

        result = apply_ignore_patterns(files, patterns)
        assert result == ["app.py", "main.py"]

    def test_keeps_all_files_when_no_patterns(self):
        """Should return all files when patterns list is empty."""
        files = ["app.py", "debug.log"]
        result = apply_ignore_patterns(files, [])
        assert result == files

    def test_handles_multiple_patterns(self):
        """Should apply multiple patterns cumulatively."""
        files = ["app.py", "debug.log", "temp.tmp", "__pycache__/cache.pyc"]
        patterns = ["*.log", "*.tmp"]

        result = apply_ignore_patterns(files, patterns)
        assert result == ["app.py", "__pycache__/cache.pyc"]
