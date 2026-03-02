"""Config file loading and management for LazyPR."""

import sys
from pathlib import Path
from typing import Optional

# tomllib is in stdlib for Python 3.11+
if sys.version_info >= (3, 11):
    import tomllib
else:
    # For older Python versions, we'd need tomli, but we'll assume 3.11+
    import tomllib


def load_config_file(path: Path) -> dict:
    """Load and parse a TOML config file.

    Args:
        path: Path to the config file.

    Returns:
        Dictionary with config values, or empty dict if file doesn't exist
        or is malformed.
    """
    if not path.exists():
        return {}

    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except Exception as e:
        import sys

        print(f"Warning: Failed to parse config file {path}: {e}", file=sys.stderr)
        return {}


def get_merged_config() -> dict:
    """Get merged configuration from global and project config files.

    Config precedence (later overrides earlier):
    - Global config (~/.lazypr)
    - Project config (./.lazypr)

    Returns:
        Merged dictionary with all config values.
    """
    global_path = Path.home() / ".lazypr"
    project_path = Path(".lazypr")

    global_config = load_config_file(global_path)
    project_config = load_config_file(project_path)

    # Project config overrides global config
    merged = global_config.copy()
    merged.update(project_config)
    return merged


def ensure_in_gitignore() -> None:
    """Ensure .lazypr is in .gitignore to prevent accidental commits.

    If .gitignore doesn't exist, it will be created.
    If .lazypr is not in .gitignore, it will be added.
    """
    gitignore_path = Path(".gitignore")

    entry = ".lazypr"

    if gitignore_path.exists():
        try:
            content = gitignore_path.read_text()
            # Check if already present (handle various formats)
            lines = content.splitlines()
            for line in lines:
                if line.strip() == entry or line.strip() == f"/{entry}":
                    return  # Already present

            # Add to .gitignore
            with open(gitignore_path, "a") as f:
                # Add newline if file doesn't end with one
                if content and not content.endswith("\n"):
                    f.write("\n")
                f.write(f"{entry}\n")
        except Exception:
            # Silently fail - not critical
            pass
    else:
        # Create .gitignore with .lazypr entry
        try:
            with open(gitignore_path, "w") as f:
                f.write(f"{entry}\n")
        except Exception:
            # Silently fail - not critical
            pass


def get_github_token() -> Optional[str]:
    """Get GitHub token from config files or environment.

    Precedence (highest to lowest):
    1. Project config (./.lazypr) github_token
    2. Global config (~/.lazypr) github_token
    3. GITHUB_TOKEN environment variable

    If token is found in a config file, ensure_in_gitignore() is called
    to prevent accidental commits.

    Returns:
        The GitHub token if found, None otherwise.
    """
    import os

    # Check config files first
    global_path = Path.home() / ".lazypr"
    project_path = Path(".lazypr")

    project_config = load_config_file(project_path)
    if "github_token" in project_config and project_config["github_token"]:
        ensure_in_gitignore()
        return project_config["github_token"]

    global_config = load_config_file(global_path)
    if "github_token" in global_config and global_config["github_token"]:
        # For global config, we still want to ensure project .gitignore has it
        # in case they copy the config file to project
        if project_path.exists():
            ensure_in_gitignore()
        return global_config["github_token"]

    # Fall back to environment variable
    env_token = os.environ.get("GITHUB_TOKEN")
    if env_token:
        return env_token

    return None
