# LazyPR

AI-powered PR creation from git diffs. Automatically generates PR titles and descriptions using AI, then opens a browser for review.

https://github.com/user-attachments/assets/a0df1b3b-5d84-431c-9501-5799c9358011

## Prerequisites

- **Git** — must be installed and available in PATH
- **GitHub CLI (`gh`)** — the setup script installs this for you

## Installation

```bash
curl -fsSL https://raw.githubusercontent.com/MarcusXavierr/lazypr/main/setup.sh | bash
```

Or clone and run locally:

```bash
git clone https://github.com/MarcusXavierr/lazypr.git
cd lazypr
bash setup.sh
```

The script installs `gh` (if needed) and the `lazypr` binary.

## Uninstall

```bash
curl -fsSL https://raw.githubusercontent.com/MarcusXavierr/lazypr/main/scripts/uninstall.sh | bash
```

Or if you cloned the repo:

```bash
bash scripts/uninstall.sh
```

## GitHub Authentication

The setup script will prompt you to authenticate with `gh`. You can also do it manually:

```bash
gh auth login
```

<details>
<summary>Manual setup with a Personal Access Token</summary>

1. Go to GitHub.com → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Select the `repo` scope (or `public_repo` for public repos only)
4. Copy the token and add it to your shell config:

```bash
# ~/.zshrc or ~/.bashrc
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
```

Then reload: `source ~/.zshrc`

> For full details on available scopes, see [GitHub's documentation](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/scopes-for-oauth-apps#available-scopes).

</details>

## Configuration

Set the following environment variables:

- `LAZYPR_MODEL` — AI model identifier (e.g., `openai:gpt-4.1`)
- `$MODEL_PROVIDER_API_KEY` — API key for your chosen provider
- `LAZYPR_MAX_DIFF_LINES` — Max diff lines per file before excluding it (default: 1000)

Provider-specific API key variables:

- `OPENAI_API_KEY` for OpenAI models
- `ANTHROPIC_API_KEY` for Anthropic models
- `CEREBRAS_API_KEY` for Cerebras models
- `GEMINI_API_KEY` for Google Gemini models
- `DEEPSEEK_API_KEY` for DeepSeek models

### Config File

Create a `.lazypr` file in your repo root or home directory:

```env
GITHUB_TOKEN=ghp_your_personal_access_token
```

**Precedence (highest to lowest):** `./.lazypr` → `~/.lazypr` → environment variables

When a token is found in a config file, lazypr automatically adds `.lazypr` to `.gitignore`.

## Models and Providers

LazyPR uses PydanticAI and supports multiple AI providers. Set your model with `LAZYPR_MODEL` in the format `provider:model-name`.

<details>
<summary>View supported models</summary>

### OpenAI

| Model | Environment Variable |
|-------|----------------------|
| `openai:gpt-4.1` | `OPENAI_API_KEY` |
| `openai:gpt-4.1-mini` | `OPENAI_API_KEY` |
| `openai:gpt-4o` | `OPENAI_API_KEY` |
| `openai:gpt-4o-mini` | `OPENAI_API_KEY` |
| `openai:o3` | `OPENAI_API_KEY` |
| `openai:o3-mini` | `OPENAI_API_KEY` |
| `openai:o4-mini` | `OPENAI_API_KEY` |
| `openai:o1` | `OPENAI_API_KEY` |

### Anthropic

| Model | Environment Variable |
|-------|----------------------|
| `anthropic:claude-opus-4` | `ANTHROPIC_API_KEY` |
| `anthropic:claude-sonnet-4-5` | `ANTHROPIC_API_KEY` |
| `anthropic:claude-3-7-sonnet-latest` | `ANTHROPIC_API_KEY` |
| `anthropic:claude-3-5-haiku-latest` | `ANTHROPIC_API_KEY` |
| `anthropic:claude-3-opus-latest` | `ANTHROPIC_API_KEY` |

### Google Gemini

| Model | Environment Variable |
|-------|----------------------|
| `google-gla:gemini-2.5-pro` | `GEMINI_API_KEY` |
| `google-gla:gemini-2.5-flash` | `GEMINI_API_KEY` |
| `google-gla:gemini-2.0-flash` | `GEMINI_API_KEY` |

### Cerebras

| Model | Environment Variable |
|-------|----------------------|
| `cerebras:llama-3.3-70b` | `CEREBRAS_API_KEY` |
| `cerebras:qwen-3-32b` | `CEREBRAS_API_KEY` |
| `cerebras:zai-glm-4.7` | `CEREBRAS_API_KEY` |

### DeepSeek

| Model | Environment Variable |
|-------|----------------------|
| `deepseek:deepseek-chat` | `DEEPSEEK_API_KEY` |
| `deepseek:deepseek-reasoner` | `DEEPSEEK_API_KEY` |

### Ollama (Local)

| Model | Environment Variable |
|-------|----------------------|
| `ollama:llama3.2` | Not required (local) |
| `ollama:phi4` | Not required (local) |
| `ollama:deepseek-r1` | Not required (local) |

Make sure Ollama is installed and the model is downloaded before using local models.

</details>

## Usage

```bash
export LAZYPR_MODEL="openai:gpt-4.1"
export OPENAI_API_KEY="sk-..."

lazypr --base main
```

## Features

- Validates git repository, `gh` CLI installation, and authentication
- Filters out files with large diffs (configurable via `LAZYPR_MAX_DIFF_LINES`)
- Supports `.lazyprignore` for excluding files (gitignore-style patterns)
- Supports `.lazypr` config file for project-specific settings
- Uses PydanticAI for structured AI output
- Opens browser for PR review with the `-w` flag

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

Create a `.lazypr` file in your repo root or home directory:

```env
GITHUB_TOKEN=ghp_your_personal_access_token
```

| Option | Description | Fallback |
|--------|-------------|----------|
| `GITHUB_TOKEN` | GitHub personal access token | `GITHUB_TOKEN` env var |

## Development

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Run all tests
pytest tests/ -v

# Run a specific test file or test
pytest tests/test_diff.py -v
pytest tests/test_diff.py::test_function_name -v
```
