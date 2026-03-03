"""Configuration functions for LazyPR."""

import os
from typing import Optional

from .config_file import get_github_token as _get_github_token_from_config


def get_max_diff_lines() -> int:
    """Get max diff lines from environment variable."""
    value = os.environ.get("LAZYPR_MAX_DIFF_LINES", "1000")
    try:
        return int(value)
    except ValueError:
        return 1000


def get_model_name() -> Optional[str]:
    """Get ZAI model name from environment variable."""
    return os.environ.get("LAZYPR_MODEL")


def get_api_key() -> Optional[str]:
    """Get API key from environment variable."""
    return os.environ.get("LAZYPR_API_KEY")


def get_github_token() -> Optional[str]:
    """Get GitHub token from config files or environment variable.

    Precedence (highest to lowest):
    1. Project config (./.lazypr) GITHUB_TOKEN
    2. Global config (~/.lazypr) GITHUB_TOKEN
    3. GITHUB_TOKEN environment variable

    Returns:
        The GitHub token if found, None otherwise.
    """
    return _get_github_token_from_config()
