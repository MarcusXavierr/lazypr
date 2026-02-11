"""Configuration functions for LazyPR."""

import os
from typing import Optional


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
