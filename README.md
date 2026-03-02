# LazyPR

AI-powered PR creation from git diffs. Automatically generates PR titles and descriptions using AI, then opens a browser for review.

## Prerequisites

Before installing LazyPR, you need:

- **Git** - Must be installed and available in PATH
- **GitHub CLI (`gh`)** - Required for creating PRs via the GitHub API

### Installing GitHub CLI

The easiest way to install the GitHub CLI is using our setup script:

```bash
# Install via curl (no clone required)
curl -fsSL https://raw.githubusercontent.com/MarcusXavierr/lazypr/main/setup.sh | bash
```

Or clone and run locally:

```bash
git clone https://github.com/MarcusXavierr/lazypr.git
cd lazypr
bash setup.sh
```

The script will:
- Detect your operating system (macOS or Linux)
- Install `gh` using the appropriate package manager
- Prompt you to authenticate with GitHub (optional)

Supported platforms:
- macOS (via Homebrew or direct download)
- Ubuntu/Debian (via apt)
- Fedora/RHEL/CentOS (via dnf/yum)
- Alpine Linux (via apk)
- Arch Linux (via pacman)
- Generic Linux (via GitHub releases)

### GitHub Authentication

After installing `gh`, you need to authenticate with GitHub. Choose one of the following methods:

**Method 1: Interactive Login (Recommended)**

```bash
gh auth login
```

This opens a browser for OAuth authentication and securely stores your credentials.

**Method 2: Personal Access Token (Manual)**

1. Go to GitHub.com → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Select the `repo` scope for full repository access (or `public_repo` for public repositories only)
4. Generate and copy the token
5. Configure the environment variable in your shell config:

> **Note:** For full details on available scopes, see [GitHub's documentation on scopes](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/scopes-for-oauth-apps#available-scopes).

```bash
# For zsh (~/.zshrc)
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"

# For bash (~/.bashrc)
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"

# For fish (~/.config/fish/config.fish)
set -x GITHUB_TOKEN "ghp_xxxxxxxxxxxxxxxxxxxx"
```

Then reload your shell configuration:

```bash
source ~/.zshrc  # or ~/.bashrc
```

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
