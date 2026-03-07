# Design: `-y` and `--dry-run` flags

## Overview

Add two new flags to the `lazypr create` command to give users more control over PR creation behavior.

## New CLI Signature

```python
@app.command(name="create")
def create_cmd(
    base: str = typer.Option(..., "--base", help="Base branch to compare against"),
    lang: str = typer.Option("en", "--lang", ...),
    yes: bool = typer.Option(False, "-y", help="Create PR directly in terminal without opening browser. Auto-confirms branch push."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show generated title and description without creating the PR."),
)
```

## Flag Behavior

### `--dry-run`

- Runs the full flow up to and including AI generation
- Prints title and description
- Stops — no branch push, no PR creation
- Takes precedence over `-y` if both are passed (silently)

### `-y`

- Auto-confirms the branch push prompt (no interactive confirmation)
- Omits the `-w` flag from `gh pr create`, creating the PR in terminal instead of opening the browser

### Both together

`--dry-run` wins silently. `-y` is ignored.

## Implementation Changes

### `__init__.py`

1. Add `yes: bool` and `dry_run: bool` parameters to `create_cmd()` and `create()`.
2. In `create()`:
   - If `dry_run`: after printing title/description, return early (skip push and PR creation).
   - Branch push confirmation: if `yes` (and not `dry_run`), skip `typer.confirm` and push directly.
3. Pass `web=not yes` to `create_pr()`.

### `create_pr()`

Add `web: bool = True` parameter. When `web=False`, omit `-w` from the `gh pr create` subprocess call.

### Open PR in browser after `-y` creation

After `create_pr()` succeeds in the `-y` (non-web) path, run `gh pr view --web` to open the newly created PR in the browser. This gives the user immediate browser access without the interactive browser-open delay during creation.
