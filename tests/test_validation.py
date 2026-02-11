"""Tests for git and gh CLI validation."""
import subprocess
import pytest
from unittest.mock import patch, MagicMock

from lazypr import (
    is_git_repo,
    has_gh_cli,
    gh_is_authenticated,
    has_remote,
    get_current_branch,
    has_commits_ahead,
    ValidationError,
)


class TestIsGitRepo:
    """Tests for is_git_repo() function."""

    def test_returns_true_when_in_git_repo(self):
        """Should return True when .git directory exists."""
        with patch("src.lazypr.validation.os.path.isdir") as mock_isdir:
            mock_isdir.return_value = True
            assert is_git_repo() is True

    def test_returns_false_when_not_in_git_repo(self):
        """Should return False when .git directory doesn't exist."""
        with patch("src.lazypr.validation.os.path.isdir") as mock_isdir:
            mock_isdir.return_value = False
            assert is_git_repo() is False


class TestHasGhCli:
    """Tests for has_gh_cli() function."""

    def test_returns_true_when_gh_installed(self):
        """Should return True when gh command is available."""
        with patch("src.lazypr.validation.shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/gh"
            assert has_gh_cli() is True

    def test_returns_false_when_gh_not_installed(self):
        """Should return False when gh command is not found."""
        with patch("src.lazypr.validation.shutil.which") as mock_which:
            mock_which.return_value = None
            assert has_gh_cli() is False


class TestGhIsAuthenticated:
    """Tests for gh_is_authenticated() function."""

    def test_returns_true_when_authenticated(self):
        """Should return True when 'gh auth status' succeeds."""
        with patch("src.lazypr.validation.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            assert gh_is_authenticated() is True

    def test_returns_false_when_not_authenticated(self):
        """Should return False when 'gh auth status' fails."""
        with patch("src.lazypr.validation.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "gh")
            assert gh_is_authenticated() is False


class TestHasRemote:
    """Tests for has_remote() function."""

    def test_returns_true_when_remote_exists(self):
        """Should return True when origin remote is configured."""
        with patch("src.lazypr.validation.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="origin\n"
            )
            assert has_remote("origin") is True

    def test_returns_false_when_remote_missing(self):
        """Should return False when remote doesn't exist."""
        with patch("src.lazypr.validation.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="")
            assert has_remote("origin") is False


class TestGetCurrentBranch:
    """Tests for get_current_branch() function."""

    def test_returns_branch_name(self):
        """Should return current branch name."""
        with patch("src.lazypr.validation.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="feature-branch\n"
            )
            assert get_current_branch() == "feature-branch"

    def test_raises_error_when_not_in_repo(self):
        """Should raise ValidationError when git command fails."""
        with patch("src.lazypr.validation.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(128, "git")
            with pytest.raises(ValidationError):
                get_current_branch()


class TestHasCommitsAhead:
    """Tests for has_commits_ahead() function."""

    def test_returns_true_when_commits_ahead(self):
        """Should return True when branch has commits ahead of base."""
        with patch("src.lazypr.validation.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="abc123\ndef456\n"
            )
            assert has_commits_ahead("main") is True

    def test_returns_false_when_no_commits(self):
        """Should return False when no commits ahead of base."""
        with patch("src.lazypr.validation.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=""
            )
            assert has_commits_ahead("main") is False
