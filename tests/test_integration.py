"""Integration tests for the complete workflow."""
import pytest
from unittest.mock import patch, MagicMock

from lazypr import create, ValidationError


class TestMainWorkflow:
    """Tests for the complete CLI workflow."""

    @pytest.mark.asyncio
    async def test_successful_workflow(self):
        """Should complete full workflow when all validations pass."""
        mock_pr_content = MagicMock()
        mock_pr_content.title = "Test PR"
        mock_pr_content.description = "Test description"

        with patch("lazypr.is_git_repo", return_value=True), \
             patch("lazypr.has_gh_cli", return_value=True), \
             patch("lazypr.gh_is_authenticated", return_value=True), \
             patch("lazypr.has_remote", return_value=True), \
             patch("lazypr.get_current_branch", return_value="feature-branch"), \
             patch("lazypr.has_commits_ahead", return_value=True), \
             patch("lazypr.get_diff_remote", return_value="diff content"), \
             patch("lazypr.parse_diff_lines", return_value={"file.py": 5}), \
             patch("lazypr.filter_large_files", return_value="filtered diff"), \
             patch("lazypr.load_ignore_patterns", return_value=[]), \
             patch("lazypr.apply_ignore_patterns", return_value=["file.py"]), \
             patch("lazypr.generate_pr_content", return_value=mock_pr_content), \
             patch("lazypr.create_pr") as mock_create_pr:

            await create(base="main")
            mock_create_pr.assert_called_once_with(
                "Test PR",
                "Test description",
                "main"
            )

    @pytest.mark.asyncio
    async def test_fails_when_not_in_git_repo(self):
        """Should exit with error when not in git repo."""
        with patch("lazypr.is_git_repo", return_value=False):
            with pytest.raises(ValidationError, match="git repository"):
                await create(base="main")

    @pytest.mark.asyncio
    async def test_fails_when_gh_cli_missing(self):
        """Should exit with error when gh CLI not installed."""
        with patch("lazypr.is_git_repo", return_value=True), \
             patch("lazypr.has_gh_cli", return_value=False):
            with pytest.raises(ValidationError, match="gh CLI"):
                await create(base="main")

    @pytest.mark.asyncio
    async def test_fails_when_gh_not_authenticated(self):
        """Should exit with error when gh not authenticated."""
        with patch("lazypr.is_git_repo", return_value=True), \
             patch("lazypr.has_gh_cli", return_value=True), \
             patch("lazypr.gh_is_authenticated", return_value=False):
            with pytest.raises(ValidationError, match="authenticated"):
                await create(base="main")

    @pytest.mark.asyncio
    async def test_fails_when_no_commits_ahead(self):
        """Should exit with error when no commits ahead of base."""
        with patch("lazypr.is_git_repo", return_value=True), \
             patch("lazypr.has_gh_cli", return_value=True), \
             patch("lazypr.gh_is_authenticated", return_value=True), \
             patch("lazypr.has_remote", return_value=True), \
             patch("lazypr.get_current_branch", return_value="feature"), \
             patch("lazypr.has_commits_ahead", return_value=False):
            with pytest.raises(ValidationError, match="commits ahead"):
                await create(base="main")
