# Binary Distribution & Release Automation

**Date:** 2026-03-06
**Status:** Approved

## Problem

Users need Python 3.13 installed to install and run lazypr. Version conflicts with other Python versions in the machine break the tool. The goal is to distribute a single self-contained binary that requires no Python on the host (only `gh` CLI).

## Scope

- Package lazypr as a single binary using PyInstaller
- Automate releases via GitHub Actions triggered by git tags
- Provide a `curl | bash` install script for users

## Out of Scope

- Windows support (Linux x86_64 + macOS x86_64/arm64 only)
- Auto-updating mechanism
- Homebrew formula (future work)

---

## Section 1: PyInstaller Configuration

### Entry Point

Create `src/lazypr/__main__.py` to serve as the PyInstaller entry point:

```python
from lazypr import main

if __name__ == "__main__":
    main()
```

### Spec File (`lazypr.spec`)

PyInstaller uses a spec file for reproducible builds with full control over hidden imports:

```python
# lazypr.spec
a = Analysis(
    ['src/lazypr/__main__.py'],
    pathex=['src'],
    hiddenimports=[
        # pydantic-ai providers (dynamically imported based on LAZYPR_MODEL env var)
        'pydantic_ai.models.openai',
        'pydantic_ai.models.anthropic',
        'pydantic_ai.models.google',
        'pydantic_ai.models.gemini',
        'pydantic_ai.models.cerebras',
        'pydantic_ai.models.deepseek',
        'pydantic_ai.models.ollama',
        # pydantic internals lost by reflection
        'pydantic._internal._generate_schema',
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name='lazypr',
    debug=False,
    strip=True,
    upx=True,
    console=True,
    onefile=True,
)
```

**Why hidden imports:** `pydantic-ai` resolves the AI provider at runtime from the `LAZYPR_MODEL` env var string (e.g. `"anthropic:claude-3-5-haiku-latest"`). PyInstaller cannot detect these dynamic imports statically, so they must be declared explicitly.

**Excluded providers:** `groq`, `mistral`, `bedrock`, `cohere` — omitted to keep binary size down. Can be added later if needed.

### Local Build Script (`scripts/build.sh`)

```bash
#!/usr/bin/env bash
set -e

echo "Installing dependencies..."
pip install -e . pyinstaller -q

echo "Building lazypr binary..."
pyinstaller lazypr.spec --distpath dist --noconfirm

echo ""
echo "Build complete: dist/lazypr"
echo "Testing binary..."
./dist/lazypr --help
```

Run before pushing a tag to verify the binary works locally.

---

## Section 2: GitHub Actions Release Workflow

File: `.github/workflows/release.yml`

### Trigger

Activated on any tag matching `v*` (e.g. `v1.0.0`, `v1.2.3`).

### Matrix Strategy

| Runner | Artifact Name |
|---|---|
| `ubuntu-latest` | `lazypr-linux-x86_64` |
| `macos-13` | `lazypr-macos-x86_64` |
| `macos-latest` | `lazypr-macos-arm64` |

`macos-13` is the last GitHub-hosted Intel macOS runner. `macos-latest` is Apple Silicon (M-series).

### Workflow

```yaml
name: Release

on:
  push:
    tags: ['v*']
  workflow_dispatch:
    inputs:
      tag:
        description: 'Tag to build and release (e.g. v1.2.0)'
        required: true
        type: string

jobs:
  build:
    strategy:
      matrix:
        include:
          - os: ubuntu-latest
            artifact_name: lazypr-linux-x86_64
          - os: macos-13
            artifact_name: lazypr-macos-x86_64
          - os: macos-latest
            artifact_name: lazypr-macos-arm64

    runs-on: ${{ matrix.os }}

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install dependencies
        run: pip install -e . pyinstaller

      - name: Build binary
        run: pyinstaller lazypr.spec --distpath dist --noconfirm

      - name: Rename binary
        run: mv dist/lazypr dist/${{ matrix.artifact_name }}

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: ${{ matrix.artifact_name }}
          path: dist/${{ matrix.artifact_name }}

  release:
    needs: build
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - uses: actions/download-artifact@v4
        with:
          merge-multiple: true
          path: dist/

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          files: dist/*
          generate_release_notes: true
```

### Release Flow (Developer)

```bash
git tag v1.2.0
git push --tags
# GitHub Actions builds 3 binaries in parallel and publishes the release automatically
```

---

## Section 3: Versioning

### Problem

`pyproject.toml` has a hardcoded `version = "0.1.0"`. Keeping it in sync with git tags manually is error-prone.

### Solution: `setuptools-scm`

Reads version directly from the git tag. The git tag becomes the single source of truth.

```toml
# pyproject.toml changes
[build-system]
requires = ["setuptools>=64", "setuptools-scm>=8"]
build-backend = "setuptools.backends.legacy:build"

[tool.setuptools_scm]
write_to = "src/lazypr/_version.py"
```

Add `src/lazypr/_version.py` to `.gitignore` since it is auto-generated.

---

## Section 4: User Install Script

File: `scripts/install.sh` — served via GitHub raw URL.

```bash
#!/usr/bin/env bash
set -e

REPO="MarcusXavierr/lazypr"
INSTALL_DIR="${LAZYPR_INSTALL_DIR:-$HOME/.local/bin}"

detect_platform() {
    local os arch
    os=$(uname -s)
    arch=$(uname -m)

    case "$os" in
        Linux)  echo "linux-x86_64" ;;
        Darwin)
            case "$arch" in
                arm64)  echo "macos-arm64" ;;
                x86_64) echo "macos-x86_64" ;;
                *) echo "Unsupported macOS arch: $arch" >&2; exit 1 ;;
            esac ;;
        *) echo "Unsupported OS: $os" >&2; exit 1 ;;
    esac
}

get_latest_version() {
    curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" \
        | grep '"tag_name"' \
        | cut -d'"' -f4
}

PLATFORM=$(detect_platform)
VERSION=$(get_latest_version)
BINARY_URL="https://github.com/$REPO/releases/download/$VERSION/lazypr-$PLATFORM"

echo "Installing lazypr $VERSION for $PLATFORM..."

mkdir -p "$INSTALL_DIR"
curl -fsSL "$BINARY_URL" -o "$INSTALL_DIR/lazypr"
chmod +x "$INSTALL_DIR/lazypr"

echo "Installed: $INSTALL_DIR/lazypr"

if ! echo "$PATH" | grep -q "$INSTALL_DIR"; then
    echo ""
    echo "Add this to your shell config (~/.zshrc or ~/.bashrc):"
    echo "  export PATH=\"$INSTALL_DIR:\$PATH\""
fi
```

**User experience:**

```bash
curl -fsSL https://raw.githubusercontent.com/MarcusXavierr/lazypr/main/scripts/install.sh | bash
```

Supports custom install directory:

```bash
LAZYPR_INSTALL_DIR=/usr/local/bin curl -fsSL ... | bash
```

---

## Files to Create / Modify

| File | Action |
|---|---|
| `src/lazypr/__main__.py` | Create — PyInstaller entry point |
| `lazypr.spec` | Create — PyInstaller spec |
| `scripts/build.sh` | Create — local build helper |
| `scripts/install.sh` | Create — user install script |
| `.github/workflows/release.yml` | Create — release automation |
| `pyproject.toml` | Modify — add setuptools-scm |
| `.gitignore` | Modify — add `src/lazypr/_version.py` and `dist/` |

## Implementation Order

1. `__main__.py` + `lazypr.spec` — get the binary building locally
2. `scripts/build.sh` — validate build works
3. `pyproject.toml` + setuptools-scm — fix versioning
4. `.github/workflows/release.yml` — automate releases
5. `scripts/install.sh` — user-facing install script
