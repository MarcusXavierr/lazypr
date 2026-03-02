"""Tests for config file loading and management."""
import os
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock, call

import pytest

from lazypr.config_file import (
    load_config_file,
    get_merged_config,
    ensure_in_gitignore,
    get_github_token,
)


class TestLoadConfigFile:
    """Tests for load_config_file() function."""

    def test_returns_empty_when_file_missing(self):
        """Should return empty dict when config file doesn't exist."""
        with patch("lazypr.config_file.Path.exists") as mock_exists:
            mock_exists.return_value = False
            result = load_config_file(Path("/fake/.lazypr"))
            assert result == {}

    def test_parses_toml_correctly(self):
        """Should parse valid TOML and return dict."""
        toml_content = 'github_token = "ghp_test_token_123"\n'
        with patch("lazypr.config_file.Path.exists") as mock_exists:
            mock_exists.return_value = True
            with patch("builtins.open", mock_open(read_data=toml_content)):
                with patch("lazypr.config_file.tomllib.load") as mock_load:
                    mock_load.return_value = {"github_token": "ghp_test_token_123"}
                    result = load_config_file(Path("/fake/.lazypr"))
                    assert result == {"github_token": "ghp_test_token_123"}

    def test_warns_on_invalid_toml(self, capsys):
        """Should print warning and return empty dict on invalid TOML."""
        with patch("lazypr.config_file.Path.exists") as mock_exists:
            mock_exists.return_value = True
            with patch("builtins.open", mock_open(read_data="invalid toml {{")):
                with patch("lazypr.config_file.tomllib.load") as mock_load:
                    mock_load.side_effect = Exception("TOML parse error")
                    result = load_config_file(Path("/fake/.lazypr"))
                    assert result == {}
                    captured = capsys.readouterr()
                    assert "Warning" in captured.err or "warning" in captured.err.lower()


class TestGetMergedConfig:
    """Tests for get_merged_config() function."""

    def test_global_only(self):
        """Should return global config when project config missing."""
        with patch("lazypr.config_file.load_config_file") as mock_load:
            mock_load.side_effect = [
                {"github_token": "global_token"},  # global
                {},  # project
            ]
            result = get_merged_config()
            assert result == {"github_token": "global_token"}

    def test_project_overrides_global(self):
        """Project config should override global config."""
        with patch("lazypr.config_file.load_config_file") as mock_load:
            mock_load.side_effect = [
                {"github_token": "global_token"},  # global
                {"github_token": "project_token"},  # project
            ]
            result = get_merged_config()
            assert result == {"github_token": "project_token"}

    def test_both_missing(self):
        """Should return empty dict when both configs missing."""
        with patch("lazypr.config_file.load_config_file") as mock_load:
            mock_load.return_value = {}
            result = get_merged_config()
            assert result == {}

    def test_project_extends_global(self):
        """Project config can add keys not in global."""
        with patch("lazypr.config_file.load_config_file") as mock_load:
            mock_load.side_effect = [
                {"github_token": "global_token"},  # global
                {"other_key": "value"},  # project
            ]
            result = get_merged_config()
            # Project config merges with global (update() behavior)
            assert result == {"github_token": "global_token", "other_key": "value"}


class TestEnsureInGitignore:
    """Tests for ensure_in_gitignore() function."""

    def test_adds_when_missing(self):
        """Should add .lazypr to .gitignore when not present."""
        gitignore_content = "*.pyc\n__pycache__/\n"
        mock_file = MagicMock()
        mock_file.__enter__ = MagicMock(return_value=mock_file)
        mock_file.__exit__ = MagicMock(return_value=False)
        mock_file.read.return_value = gitignore_content

        with patch("lazypr.config_file.Path.exists") as mock_exists:
            mock_exists.return_value = True
            with patch("builtins.open", return_value=mock_file):
                ensure_in_gitignore()
                # Should have written the updated content
                mock_file.write.assert_called_once()
                written = mock_file.write.call_args[0][0]
                assert ".lazypr" in written

    def test_skips_when_present(self):
        """Should not modify .gitignore when .lazypr already present."""
        gitignore_content = "*.pyc\n.lazypr\n__pycache__/\n"

        # Track if write was called via Path.write_text (simulating append)
        write_called = False
        original_write_text = Path.write_text

        def mock_write_text(self, content):
            nonlocal write_called
            write_called = True
            return original_write_text(self, content)

        with patch("lazypr.config_file.Path.exists") as mock_exists:
            mock_exists.return_value = True
            with patch.object(Path, "read_text", return_value=gitignore_content):
                with patch.object(Path, "write_text", mock_write_text):
                    ensure_in_gitignore()
                    assert not write_called, "Should not have written to .gitignore"

    def test_creates_gitignore_when_missing(self):
        """Should create .gitignore with .lazypr entry if .gitignore doesn't exist."""
        mock_file = MagicMock()
        mock_file.__enter__ = MagicMock(return_value=mock_file)
        mock_file.__exit__ = MagicMock(return_value=False)

        with patch("lazypr.config_file.Path.exists") as mock_exists:
            mock_exists.side_effect = [False, True]  # First for gitignore, second check
            with patch("builtins.open", return_value=mock_file):
                ensure_in_gitignore()
                mock_file.write.assert_called_once()
                written = mock_file.write.call_args[0][0]
                assert ".lazypr" in written


class TestGetGithubToken:
    """Tests for get_github_token() function."""

    def test_from_env_var(self):
        """Should return token from GITHUB_TOKEN env var when no config."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "env_token"}):
            with patch("lazypr.config_file.load_config_file") as mock_load:
                mock_load.return_value = {}
                result = get_github_token()
                assert result == "env_token"

    def test_from_project_config(self):
        """Should prefer project config over env var."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "env_token"}):
            with patch("lazypr.config_file.load_config_file") as mock_load:
                # Note: get_github_token() checks project first, then global
                mock_load.side_effect = [
                    {"github_token": "project_token"},  # project config (checked first)
                    {},  # global config (checked second, won't be reached)
                ]
                with patch("lazypr.config_file.ensure_in_gitignore") as mock_gitignore:
                    result = get_github_token()
                    assert result == "project_token"
                    mock_gitignore.assert_called_once()

    def test_from_global_config(self):
        """Should use global config when project config missing."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("lazypr.config_file.load_config_file") as mock_load:
                # Both configs checked, global has token
                mock_load.side_effect = [
                    {"github_token": "global_token"},  # global config
                    {},  # project config (empty)
                ]
                with patch("lazypr.config_file.ensure_in_gitignore") as mock_gitignore:
                    result = get_github_token()
                    assert result == "global_token"
                    mock_gitignore.assert_called_once()

    def test_returns_none_when_no_token(self):
        """Should return None when no token found anywhere."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("lazypr.config_file.load_config_file") as mock_load:
                mock_load.return_value = {}
                result = get_github_token()
                assert result is None

    def test_empty_string_treated_as_missing(self):
        """Empty string should be treated as no token."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": ""}):
            with patch("lazypr.config_file.load_config_file") as mock_load:
                mock_load.return_value = {}
                result = get_github_token()
                assert result is None

    def test_empty_string_in_config_treated_as_missing(self):
        """Empty string in config should fall back to env var."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "env_token"}):
            with patch("lazypr.config_file.load_config_file") as mock_load:
                mock_load.return_value = {"github_token": ""}
                result = get_github_token()
                assert result == "env_token"
