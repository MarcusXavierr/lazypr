# LazyPR

AI-powered PR creation from git diffs. Automatically generates PR titles and descriptions using AI, then opens a browser for review.

https://github.com/user-attachments/assets/a0df1b3b-5d84-431c-9501-5799c9358011

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
- `$MODEL_PROVIDER_API_KEY` - API key for authentication (it depends on which model you're using)
- `LAZYPR_MAX_DIFF_LINES` - Maximum diff lines per file before filtering out the file (default: 1000)

### Config File

You can also use a `.lazypr` file for configuration. See [.lazypr Config File](#lazypr-config-file) section below for details.

**Note:** `LAZYPR_API_KEY` is optional. You can use provider-specific environment variables instead:
- `CEREBRAS_API_KEY` for Cerebras models
- `OPENAI_API_KEY` for OpenAI models
- `ANTHROPIC_API_KEY` for Anthropic models
- etc.

## Models and Providers

LazyPR uses PydanticAI to support multiple AI providers. Configure your model using the `LAZYPR_MODEL` environment variable in the format `provider:model-name`.

These are some examples of models you can use and their environment variables:

### OpenAI

| Model                                              | Environment Variable |
|----------------------------------------------------|----------------------|
| `openai:gpt-5`                                     | `OPENAI_API_KEY`     |
| `openai:gpt-5-mini`                                | `OPENAI_API_KEY`     |
| `openai:gpt-5-nano`                                | `OPENAI_API_KEY`     |
| `openai:gpt-5.1`                                   | `OPENAI_API_KEY`     |
| `openai:gpt-5.2`                                   | `OPENAI_API_KEY`     |
| `openai:gpt-4.1` (Is use it and works pretty well) | `OPENAI_API_KEY`     |
| `openai:gpt-4.1-mini`                              | `OPENAI_API_KEY`     |
| `openai:gpt-4o`                                    | `OPENAI_API_KEY`     |
| `openai:gpt-4o-mini`                               | `OPENAI_API_KEY`     |
| `openai:o3`                                        | `OPENAI_API_KEY`     |
| `openai:o3-mini`                                   | `OPENAI_API_KEY`     |
| `openai:o4-mini`                                   | `OPENAI_API_KEY`     |
| `openai:o1`                                        | `OPENAI_API_KEY`     |

### Anthropic

| Model                                | Environment Variable |
|--------------------------------------|----------------------|
| `anthropic:claude-opus-4`            | `ANTHROPIC_API_KEY`  |
| `anthropic:claude-sonnet-4-5`        | `ANTHROPIC_API_KEY`  |
| `anthropic:claude-3-7-sonnet-latest` | `ANTHROPIC_API_KEY`  |
| `anthropic:claude-3-5-haiku-latest`  | `ANTHROPIC_API_KEY`  |
| `anthropic:claude-3-opus-latest`     | `ANTHROPIC_API_KEY`  |
| `anthropic:claude-3-haiku-20240307`  | `ANTHROPIC_API_KEY`  |

### Google Gemini

| Model | Environment Variable |
|-------|---------------------|
| `google-gla:gemini-2.5-pro` | `GEMINI_API_KEY` |
| `google-gla:gemini-2.5-flash` | `GEMINI_API_KEY` |
| `google-gla:gemini-2.0-flash` | `GEMINI_API_KEY` |
| `google-gla:gemini-3-pro-preview` | `GEMINI_API_KEY` |
| `google-gla:gemini-3-flash-preview` | `GEMINI_API_KEY` |

### Cerebras

| Model | Environment Variable |
|-------|---------------------|
| `cerebras:llama-3.3-70b` | `CEREBRAS_API_KEY` |
| `cerebras:gpt-oss-120b` | `CEREBRAS_API_KEY` |
| `cerebras:qwen-3-32b` | `CEREBRAS_API_KEY` |
| `cerebras:zai-glm-4.7` | `CEREBRAS_API_KEY` |

### DeepSeek

| Model | Environment Variable |
|-------|---------------------|
| `deepseek:deepseek-chat` | `DEEPSEEK_API_KEY` |
| `deepseek:deepseek-reasoner` | `DEEPSEEK_API_KEY` |

### Ollama (Local)

| Model | Environment Variable |
|-------|---------------------|
| `ollama:llama3.2` | Not required (local) |
| `ollama:llama3.1` | Not required (local) |
| `ollama:phi4` | Not required (local) |
| `ollama:deepseek-r1` | Not required (local) |

**Note:** Ollama runs models locally. Make sure you have Ollama installed and the model downloaded.

## Usage

```bash
export LAZYPR_MODEL="cerebras:zai-glm-4.7"
export $PROVIDER_TOKEN="sk-..."

lazypr --base main
```

## Features

- Validates git repository, gh CLI installation and authentication
- Filters out files with large diffs (configurable via `LAZYPR_MAX_DIFF_LINES`)
- Supports `.lazyprignore` file with gitignore-style patterns
- Supports `.lazypr` config file for project-specific settings
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

## .lazypr Config File

Create a `.lazypr` file in your repository root or home directory for configuration:

```toml
# GitHub token for authenticating with gh CLI
github_token = "ghp_your_personal_access_token"
```

**Config precedence (highest to lowest):**
1. `./.lazypr` - Project config (checked first)
2. `~/.lazypr` - Global user config
3. Environment variables (fallback)

**Available options:**

| Option | Description | Fallback |
|--------|-------------|----------|
| `github_token` | GitHub personal access token | `GITHUB_TOKEN` env var |

When a `github_token` is found in a config file, lazypr will:
1. Use that token for `gh` CLI commands
2. Automatically add `.lazypr` to `.gitignore` (if not already present) to prevent committing secrets

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
