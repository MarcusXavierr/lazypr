"""Diff parsing and filtering functions."""

import re
import subprocess


# Custom exceptions
class DiffError(Exception):
    """Raised when diff operations fail."""
    pass


def get_diff(base: str) -> str:
    """Get diff from base branch to current HEAD."""
    try:
        result = subprocess.run(
            ["git", "diff", f"{base}...HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise DiffError(f"Failed to get diff from base branch '{base}'") from e


def _is_diff_content_line(line: str) -> bool:
    """Check if a line is part of a file's diff content (not a separator)."""
    return (
        line.startswith("index ") or
        line.startswith("--- ") or
        line.startswith("+++ ") or
        line.startswith("@@") or
        line.startswith("+") or
        line.startswith("-") or
        line.startswith(" ") or
        line == "\\ No newline at end of file"
    )


def _parse_hunk_line_count(line: str) -> int | None:
    """Extract the number of added lines from a hunk header like '@@ -1,1000 +1,1000 @@'."""
    # Match patterns like @@ -1,1000 +1,1000 @@ or @@ -1 +1 @@
    # The number after the comma in the + section is the line count
    match = re.match(r'@@ -\d+(?:,\d+)? \+\d+,?(\d+)? @@', line)
    if match:
        count_str = match.group(1)
        if count_str:
            return int(count_str)
    return None


def parse_diff_lines(diff: str) -> dict[str, int]:
    """Parse diff and return a dict mapping file paths to actual line counts."""
    file_lines: dict[str, int] = {}
    current_file: str | None = None
    current_count = 0

    # Normalize line endings and split
    lines = diff.replace("\r\n", "\n").split("\n")
    # Remove trailing empty line if present
    if lines and lines[-1] == "":
        lines = lines[:-1]

    for line in lines:
        # Check for file header
        if line.startswith("diff --git "):
            # Save previous file count
            if current_file is not None:
                file_lines[current_file] = current_count
            # Extract new file path
            match = re.match(r'diff --git a/(.*) b/(.*)', line)
            if match:
                current_file = match.group(2)
                current_count = 1  # Count the diff --git line
            else:
                current_file = None
                current_count = 0
        elif current_file is not None:
            # Check for binary files
            if line == "Binary files differ":
                # Remove binary file from tracking
                current_file = None
                current_count = 0
            elif _is_diff_content_line(line):
                current_count += 1
            # Ignore empty lines and separators between files

    # Save last file
    if current_file is not None:
        file_lines[current_file] = current_count

    return file_lines


def _get_effective_line_count(diff: str) -> dict[str, int]:
    """Get effective line count for filtering purposes.

    Uses hunk header line count when available (e.g., @@ -1,1000 +1,1000 @@ returns 1000),
    otherwise falls back to actual line count.
    """
    actual_counts = parse_diff_lines(diff)
    effective_counts: dict[str, int] = {}

    # Normalize line endings and split
    lines = diff.replace("\r\n", "\n").split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]

    current_file: str | None = None

    for line in lines:
        if line.startswith("diff --git "):
            match = re.match(r'diff --git a/(.*) b/(.*)', line)
            if match:
                current_file = match.group(2)
                effective_counts[current_file] = actual_counts.get(current_file, 0)
        elif current_file is not None and line.startswith("@@"):
            hunk_count = _parse_hunk_line_count(line)
            if hunk_count is not None and hunk_count > effective_counts.get(current_file, 0):
                effective_counts[current_file] = hunk_count

    return effective_counts


def filter_large_files(diff: str, max_lines: int) -> str:
    """Remove files from diff that exceed max_lines."""
    if not diff.strip():
        return ""

    file_lines = _get_effective_line_count(diff)
    files_to_remove = {f for f, count in file_lines.items() if count > max_lines}

    if not files_to_remove:
        return diff

    # Normalize line endings and split
    lines = diff.replace("\r\n", "\n").split("\n")
    # Remove trailing empty line if present for processing
    has_trailing_newline = lines and lines[-1] == ""
    if has_trailing_newline:
        lines = lines[:-1]

    # Collect lines for each file separately
    files_in_diff: dict[str, list[str]] = {}
    current_file: str | None = None

    for line in lines:
        if line.startswith("diff --git "):
            # Extract file path
            match = re.match(r'diff --git a/(.*) b/(.*)', line)
            if match:
                current_file = match.group(2)
                files_in_diff[current_file] = [line]
            else:
                current_file = None
        elif current_file is not None:
            files_in_diff[current_file].append(line)

    # Rebuild diff without large files
    filtered_lines: list[str] = []
    for filename, file_lines_list in files_in_diff.items():
        if filename not in files_to_remove:
            filtered_lines.extend(file_lines_list)

    if not filtered_lines:
        return ""

    return "\n".join(filtered_lines) + "\n"


def _rebuild_diff_with_files(diff: str, allowed_files: list[str]) -> str:
    """Rebuild diff including only allowed files."""
    allowed_set = set(allowed_files)
    filtered_lines: list[str] = []
    current_file: str | None = None
    include_current = False

    for line in diff.split("\n"):
        if line.startswith("diff --git "):
            match = re.match(r'diff --git a/(.*) b/(.*)', line)
            if match:
                current_file = match.group(2)
                include_current = current_file in allowed_set
            else:
                include_current = False

            if include_current:
                filtered_lines.append(line)
        elif include_current:
            filtered_lines.append(line)

    return "\n".join(filtered_lines).rstrip() + "\n" if filtered_lines else ""
