"""LazyPR - AI-powered PR creation from git diffs."""

import subprocess
import typer
from rich.console import Console

from .config import get_max_diff_lines

from .validation import (
    ValidationError,
    is_git_repo,
    has_gh_cli,
    gh_is_authenticated,
    has_remote,
    get_current_branch,
    has_commits_ahead,
)

from .diff import (
    DiffError,
    get_diff,
    parse_diff_lines,
    filter_large_files,
    _rebuild_diff_with_files,
)

from .ignore import (
    load_ignore_patterns,
    apply_ignore_patterns,
)

from .ai import (
    generate_pr_content,
)

# Create typer app and console
console = Console()
app = typer.Typer(help="AI-powered PR creation from git diffs")

# PR creation function
def create_pr(title: str, description: str, base: str) -> None:
    """Create a PR using gh CLI."""
    try:
        subprocess.run(
            [
                "gh", "pr", "create",
                "-w",
                "--base", base,
                "--title", title,
                "--body", description,
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise ValidationError(f"Failed to create PR: {e}") from e


# CLI command
@app.command(name="create")
def create_cmd(
    base: str = typer.Option(..., "--base", help="Base branch to compare against"),
) -> None:
    """Create a PR with AI-generated title and description."""
    import asyncio

    asyncio.run(create(base))


async def create(base: str) -> None:
    """Async implementation of create command."""
    # Validation checks
    if not is_git_repo():
        raise ValidationError("Not in a git repository")

    if not has_gh_cli():
        raise ValidationError("gh CLI not installed")

    if not gh_is_authenticated():
        raise ValidationError("gh CLI not authenticated. Run 'gh auth login'")

    if not has_remote("origin"):
        raise ValidationError("No 'origin' remote found")

    current_branch = get_current_branch()
    typer.echo(f"Current branch: {current_branch}")

    if not has_commits_ahead(base):
        raise ValidationError(f"No commits ahead of '{base}'")

    # Get and filter diff
    typer.echo(f"Getting diff from {base}...")
    diff = get_diff(base)

    if not diff.strip():
        raise DiffError("No changes to include in PR")

    # Filter large files
    max_lines = get_max_diff_lines()
    filtered_diff = filter_large_files(diff, max_lines)

    # Load and apply ignore patterns
    patterns = load_ignore_patterns()
    file_lines = parse_diff_lines(filtered_diff)
    filtered_files = apply_ignore_patterns(list(file_lines.keys()), patterns)

    # Rebuild diff with only allowed files
    if set(file_lines.keys()) != set(filtered_files):
        filtered_diff = _rebuild_diff_with_files(filtered_diff, filtered_files)

    if not filtered_diff.strip():
        raise DiffError("No changes left after filtering")

    with console.status("[bold green]Generating PR content with AI...", spinner="dots"):
        pr_content = await generate_pr_content(filtered_diff)

    typer.echo(f"\nTitle: {pr_content.title}")
    typer.echo(f"Description:\n{pr_content.description}\n")

    # Create PR
    typer.echo("Creating PR and opening browser...")
    create_pr(pr_content.title, pr_content.description, base)


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
