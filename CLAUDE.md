# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is LazyPR

A CLI tool that generates PR titles and descriptions from git diffs using AI (via PydanticAI), then creates the PR using `gh` CLI. Requires `git` and `gh` in PATH.

## Commands

```bash
# Install (editable/dev mode)
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run a single test
pytest tests/test_diff.py -v
pytest tests/test_diff.py::test_function_name -v

# Run the CLI
lazypr create --base main
```

## Architecture

All source code lives in `src/lazypr/`. Entry point is `lazypr:app` (Typer app defined in `__init__.py`).

**Flow:** CLI command (`__init__.py`) → validate environment (`validation.py`) → get git diff (`diff.py`) → filter large files & apply `.lazyprignore` patterns (`ignore.py`) → generate PR content via PydanticAI agent (`ai.py`) → create PR via `gh pr create`.

**Key modules:**
- `__init__.py` — CLI definition, main orchestration logic, `create_pr()` function
- `ai.py` — PydanticAI agent setup, `PRContent` model, prompt template for PR generation
- `diff.py` — Git diff retrieval (local/remote), parsing, filtering large files
- `validation.py` — Pre-flight checks (git repo, gh CLI, auth, remote, branch status)
- `ignore.py` — `.lazyprignore` file support using `pathspec` (gitignore-style patterns)
- `config.py` / `config_file.py` — Config from env vars and `.lazypr` files (project > global > env)

**Configuration:** Model set via `LAZYPR_MODEL` env var (format: `provider:model-name`). API keys use provider-specific env vars (e.g., `OPENAI_API_KEY`). Max diff lines via `LAZYPR_MAX_DIFF_LINES` (default 1000).

## Testing

Tests use `pytest` with `pytest-asyncio` and `pytest-mock`. Tests are in `tests/` and mirror source modules. The `pythonpath` is configured to `src` in `pyproject.toml`.

## Writing commits
Don't ever put the agent as co author on a commit.
