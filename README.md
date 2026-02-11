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
- `LAZYPR_API_KEY` - API key for authentication (optional)
- `LAZYPR_MAX_DIFF_LINES` - Maximum diff lines per file (default: 1000)

**Note:** `LAZYPR_API_KEY` is optional. You can use provider-specific environment variables instead:
- `ZAI_API_KEY` for Cerebras models
- `OPENAI_API_KEY` for OpenAI models
- `ANTHROPIC_API_KEY` for Anthropic models
- etc.

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

## Building

To install or rebuild the `lazypr` command:

```bash
# Install in development mode (editable)
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"

# Build package for distribution
python -m build
```

The `lazypr` command will be available in your PATH after installation.

## Development

Run tests:
```bash
pytest tests/ -v
```
