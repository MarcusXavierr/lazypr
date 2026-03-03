"""Integration tests for the complete workflow."""
import subprocess
import pytest
import typer
from unittest.mock import patch, MagicMock

from lazypr import create, create_pr, ValidationError


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
             patch("lazypr.is_branch_pushed_to_remote", return_value=True), \
             patch("lazypr.has_commits_ahead", return_value=True), \
             patch("lazypr.get_diff", return_value="diff content"), \
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
             patch("lazypr.is_branch_pushed_to_remote", return_value=True), \
             patch("lazypr.has_commits_ahead", return_value=False):
            with pytest.raises(ValidationError, match="commits ahead"):
                await create(base="main")

    @pytest.mark.asyncio
    async def test_prompts_to_push_branch_when_not_on_remote(self):
        """Should prompt user to push branch when not on remote."""
        mock_pr_content = MagicMock()
        mock_pr_content.title = "Test PR"
        mock_pr_content.description = "Test description"

        with patch("lazypr.is_git_repo", return_value=True), \
             patch("lazypr.has_gh_cli", return_value=True), \
             patch("lazypr.gh_is_authenticated", return_value=True), \
             patch("lazypr.has_remote", return_value=True), \
             patch("lazypr.get_current_branch", return_value="feature-branch"), \
             patch("lazypr.is_branch_pushed_to_remote", return_value=False) as mock_check, \
             patch("lazypr.push_branch_to_remote") as mock_push, \
             patch("lazypr.has_commits_ahead", return_value=True), \
             patch("lazypr.get_diff", return_value="diff content"), \
             patch("lazypr.parse_diff_lines", return_value={"file.py": 5}), \
             patch("lazypr.filter_large_files", return_value="filtered diff"), \
             patch("lazypr.load_ignore_patterns", return_value=[]), \
             patch("lazypr.apply_ignore_patterns", return_value=["file.py"]), \
             patch("lazypr.generate_pr_content", return_value=mock_pr_content), \
             patch("lazypr.create_pr") as mock_create_pr, \
             patch("typer.confirm", return_value=True) as mock_confirm:

            await create(base="main")
            mock_check.assert_called_once_with("feature-branch")
            mock_confirm.assert_called_once()
            mock_push.assert_called_once_with("feature-branch", "origin")
            mock_create_pr.assert_called_once()

    @pytest.mark.asyncio
    async def test_exits_when_user_declines_push(self):
        """Should exit gracefully when user declines to push."""
        mock_pr_content = MagicMock()
        mock_pr_content.title = "Test PR"
        mock_pr_content.description = "Test description"

        with patch("lazypr.is_git_repo", return_value=True), \
             patch("lazypr.has_gh_cli", return_value=True), \
             patch("lazypr.gh_is_authenticated", return_value=True), \
             patch("lazypr.has_remote", return_value=True), \
             patch("lazypr.get_current_branch", return_value="feature-branch"), \
             patch("lazypr.is_branch_pushed_to_remote", return_value=False), \
             patch("lazypr.push_branch_to_remote") as mock_push, \
             patch("lazypr.has_commits_ahead", return_value=True), \
             patch("lazypr.get_diff", return_value="diff content"), \
             patch("lazypr.parse_diff_lines", return_value={"file.py": 5}), \
             patch("lazypr.filter_large_files", return_value="filtered diff"), \
             patch("lazypr.load_ignore_patterns", return_value=[]), \
             patch("lazypr.apply_ignore_patterns", return_value=["file.py"]), \
             patch("lazypr.generate_pr_content", return_value=mock_pr_content), \
             patch("lazypr.create_pr") as mock_create_pr, \
             patch("typer.confirm", return_value=False) as mock_confirm:

            with pytest.raises(typer.Exit):
                await create(base="main")
            mock_confirm.assert_called_once()
            mock_push.assert_not_called()
            mock_create_pr.assert_not_called()


class TestConfigTokenIntegration:
    """Tests for config token integration with PR creation."""

    def test_create_pr_uses_config_token(self):
        """Should pass GITHUB_TOKEN from config to subprocess environment."""
        with patch("lazypr.get_github_token", return_value="config_token_123"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                create_pr("Test Title", "Test Description", "main")

                # Verify subprocess was called with correct env
                call_args = mock_run.call_args
                env = call_args.kwargs.get("env")
                assert env is not None
                assert env["GITHUB_TOKEN"] == "config_token_123"

    def test_create_pr_uses_env_when_no_config_token(self):
        """Should use environment GITHUB_TOKEN when no config token."""
        import os
        with patch.dict(os.environ, {"GITHUB_TOKEN": "env_token_456"}):
            with patch("lazypr.get_github_token", return_value="env_token_456"):
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)
                    create_pr("Test Title", "Test Description", "main")

                    call_args = mock_run.call_args
                    env = call_args.kwargs.get("env")
                    assert env is not None
                    assert env["GITHUB_TOKEN"] == "env_token_456"

    def test_create_pr_no_token_when_not_configured(self):
        """Should not add GITHUB_TOKEN to env when not configured."""
        with patch.dict("os.environ", {}, clear=True):  # Clear env for this test
            with patch("lazypr.get_github_token", return_value=None):
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)
                    create_pr("Test Title", "Test Description", "main")

                    call_args = mock_run.call_args
                    env = call_args.kwargs.get("env")
                    # Should still have env, but no GITHUB_TOKEN added by us
                    assert env is not None
                    assert "GITHUB_TOKEN" not in env
