"""LazyPR - AI-powered PR creation from git diffs."""

import os
import subprocess
import typer
from rich.console import Console

from .config import get_max_diff_lines, get_github_token

from .validation import (
    ValidationError,
    is_git_repo,
    has_gh_cli,
    gh_is_authenticated,
    has_remote,
    get_current_branch,
    has_commits_ahead,
    is_branch_pushed_to_remote,
    push_branch_to_remote,
)

from .diff import (
    DiffError,
    get_diff_remote,
    parse_diff_lines,
    filter_large_files,
    rebuild_diff_with_files,
)

from .ignore import (
    load_ignore_patterns,
    apply_ignore_patterns,
    matches_pattern,
)

from .ai import (
    generate_pr_content,
)

# Create typer app and console
console = Console()
app = typer.Typer(help="AI-powered PR creation from git diffs")


# PR creation function
def create_pr(title: str, description: str, base: str, web: bool = True) -> None:
    """Create a PR using gh CLI."""
    # Get GitHub token from config or environment
    token = get_github_token()

    # Prepare environment for subprocess
    env = os.environ.copy()
    if token:
        env["GITHUB_TOKEN"] = token

    cmd = ["gh", "pr", "create"]
    if web:
        cmd.append("-w")
    cmd += ["--base", base, "--title", title, "--body", description]

    try:
        subprocess.run(
            cmd,
            check=True,
            env=env,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        raise ValidationError(f"Failed to create PR: {error_msg}") from e


# Available languages for PR generation
LANGUAGE_CHOICES = ["en", "pt", "es", "fr", "de", "zh", "ja", "ko", "it", "ru"]


# CLI command
@app.command(name="create")
def create_cmd(
    base: str = typer.Option(..., "--base", help="Base branch to compare against"),
    lang: str = typer.Option(
        "en",
        "--lang",
        help="Language for the PR title and description (en, pt, es, fr, de, zh, ja, ko, it, ru)",
        case_sensitive=False,
    ),
    yes: bool = typer.Option(
        False,
        "-y",
        help="Create PR directly in terminal without opening browser. Auto-confirms branch push.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show generated title and description without creating the PR.",
    ),
) -> None:
    """Create a PR with AI-generated title and description."""
    import asyncio

    asyncio.run(create(base, lang, yes=yes, dry_run=dry_run))


async def create(
    base: str, language: str = "en", yes: bool = False, dry_run: bool = False
) -> None:
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

    # Check if branch is pushed to remote
    if not dry_run and not is_branch_pushed_to_remote(current_branch):
        if yes:
            typer.echo(f"Pushing to origin/{current_branch}...")
            push_branch_to_remote(current_branch, "origin")
            typer.echo("Push successful.")
        else:
            if not typer.confirm(
                f"Branch '{current_branch}' is not pushed to remote. Push now?"
            ):
                typer.echo("Aborted. Branch must be pushed to create a PR.")
                raise typer.Exit(1)
            typer.echo(f"Pushing to origin/{current_branch}...")
            push_branch_to_remote(current_branch, "origin")
            typer.echo("Push successful.")

    if not has_commits_ahead(base):
        raise ValidationError(f"No commits ahead of '{base}'")

    # Get and filter diff from remote base branch
    typer.echo(f"Getting diff from {base}...")
    diff = get_diff_remote(base)

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
        filtered_diff = rebuild_diff_with_files(filtered_diff, filtered_files)

    if not filtered_diff.strip():
        raise DiffError("No changes left after filtering")

    with console.status("[bold green]Generating PR content with AI...", spinner="dots"):
        pr_content = await generate_pr_content(filtered_diff, language)

    typer.echo(f"\nTitle: {pr_content.title}")
    typer.echo(f"Description:\n{pr_content.description}\n")

    if dry_run:
        return

    # Create PR
    if yes:
        typer.echo("Creating PR...")
    else:
        typer.echo("Creating PR and opening browser...")
    create_pr(pr_content.title, pr_content.description, base, web=not yes)

    if yes:
        typer.echo("Opening PR in browser...")
        subprocess.run(["gh", "pr", "view", "--web"], check=True)


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
