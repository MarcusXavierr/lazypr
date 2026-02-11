"""Ignore pattern functions for .lazyprignore file."""

from pathlib import Path

import pathspec


def load_ignore_patterns() -> list[str]:
    """Load ignore patterns from .lazyprignore file."""
    ignore_file = Path(".lazyprignore")
    if not ignore_file.exists():
        return []

    patterns: list[str] = []
    with open(ignore_file, "r") as f:
        for line in f:
            line = line.rstrip("\n\r")
            # Skip comments and empty lines
            if line and not line.startswith("#"):
                patterns.append(line)

    return patterns


def matches_pattern(pattern: str, filepath: str) -> bool:
    """Check if filepath matches a gitignore-style pattern."""
    # Handle negation patterns
    if pattern.startswith("!"):
        pattern = pattern[1:]
        # For negation, we check if it matches - caller decides meaning
        spec = pathspec.PathSpec.from_lines("gitwildmatch", [pattern])
        return spec.match_file(filepath)

    spec = pathspec.PathSpec.from_lines("gitwildmatch", [pattern])
    return spec.match_file(filepath)


def apply_ignore_patterns(files: list[str], patterns: list[str]) -> list[str]:
    """Filter out files matching ignore patterns."""
    if not patterns:
        return files

    # Separate regular patterns from negation patterns
    regular_patterns: list[str] = []
    negation_patterns: list[str] = []

    for pattern in patterns:
        if pattern.startswith("!"):
            negation_patterns.append(pattern[1:])
        else:
            regular_patterns.append(pattern)

    result: list[str] = []

    for filepath in files:
        # Check if file matches any regular pattern
        ignored = False
        for pattern in regular_patterns:
            if matches_pattern(pattern, filepath):
                ignored = True
                break

        # Check negation patterns (re-include if matches)
        if ignored:
            for pattern in negation_patterns:
                if matches_pattern(pattern, filepath):
                    ignored = False
                    break

        if not ignored:
            result.append(filepath)

    return result
