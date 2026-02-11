# LazyPR

AI-powered PR creation from git diffs. Automatically generates PR titles and descriptions using AI, then opens a browser for review.

## Installation

```bash
pip install -e .
```

For development:
```bash
pip install -e ".[dev]"
```

## Configuration

Set the following environment variables:

- `LAZYPR_MODEL` - ZAI model identifier (e.g., "cerebras:zai-glm-4.7")
- `LAZYPR_API_KEY` - API key for authentication
- `LAZYPR_MAX_DIFF_LINES` - Maximum diff lines per file (default: 1000)

## Usage

```bash
export LAZYPR_MODEL="cerebras:zai-glm-4.7"
export LAZYPR_API_KEY="sk-..."

lazypr create --base main
```

## Features

- Validates git repository, gh CLI installation and authentication
- Filters out files with large diffs (configurable via `LAZYPR_MAX_DIFF_LINES`)
- Supports `.lazyprignore` file with gitignore-style patterns
- Uses PydanticAI for structured AI output
- Opens browser for PR review with `-w` flag

## .lazyprignore

Create a `.lazyprignore` file in your repository to exclude files from the diff:

```
# Comments are supported
*.log
__pycache__/
*.tmp
!important.log  # Negation patterns work too
```

## Development

Run tests:
```bash
pytest tests/ -v
```
