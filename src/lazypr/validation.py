"""Validation functions for git and gh CLI."""

import os
import shutil
import subprocess


# Custom exceptions
class ValidationError(Exception):
    """Raised when validation fails."""
    pass


def is_git_repo() -> bool:
    """Check if we're in a git repository."""
    return os.path.isdir(".git")


def _git_command_succeeds(cmd: list[str]) -> bool:
    """Check if a git command succeeds."""
    try:
        subprocess.run(cmd, capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def has_gh_cli() -> bool:
    """Check if gh CLI is installed."""
    return shutil.which("gh") is not None


def gh_is_authenticated() -> bool:
    """Check if gh CLI is authenticated."""
    try:
        subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def has_remote(remote: str = "origin") -> bool:
    """Check if a remote is configured."""
    try:
        result = subprocess.run(
            ["git", "remote"],
            capture_output=True,
            text=True,
            check=True
        )
        remotes = result.stdout.strip().split("\n")
        return remote in remotes
    except subprocess.CalledProcessError:
        return False


def get_current_branch() -> str:
    """Get the current git branch name."""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise ValidationError("Failed to get current branch") from e


def has_commits_ahead(base: str) -> bool:
    """Check if current branch has commits ahead of base."""
    try:
        result = subprocess.run(
            ["git", "rev-list", f"{base}..HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        return len(result.stdout.strip()) > 0
    except subprocess.CalledProcessError:
        return False
