# Onedir Distribution Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Switch from PyInstaller `onefile` to `onedir` so the binary doesn't extract on every run, eliminating startup latency.

**Architecture:** PyInstaller builds a `dist/lazypr/` directory instead of a single binary. The release workflow tarballs it (wrapped as `lazypr/`) and uploads `lazypr-{platform}.tar.gz`. The install script downloads the tarball, extracts it to `~/.local/share/`, and symlinks `~/.local/bin/lazypr → ~/.local/share/lazypr/lazypr`.

**Tech Stack:** PyInstaller, Bash, GitHub Actions (`softprops/action-gh-release`).

---

### Task 1: Fix lazypr.spec for onedir

**Files:**
- Modify: `lazypr.spec`

The spec currently has leftover changes from a failed caching attempt (`import os`, `runtime_tmpdir`, `onefile=True`). Clean those up and switch to onedir.

**Step 1: Remove `import os` from top of spec**

The `import os` was only needed for `runtime_tmpdir`. Remove it.

**Step 2: Remove `onefile=True` and `runtime_tmpdir` from `EXE()`**

In the `EXE()` call, remove these two lines:
```python
    runtime_tmpdir=os.path.join(os.path.expanduser('~'), '.cache', 'lazypr'),
    onefile=True,
```

`onefile` defaults to `False` in PyInstaller, so removing it switches to onedir mode.

**Step 3: Verify the spec looks correct**

The `EXE()` block should have no `onefile` or `runtime_tmpdir` entries. The `charset_normalizer` hidden import added earlier stays.

**Step 4: Commit**

```bash
git add lazypr.spec
git commit -m "fix: switch PyInstaller to onedir mode for faster startup"
```

---

### Task 2: Update release.yml to produce tarballs

**Files:**
- Modify: `.github/workflows/release.yml`

**Step 1: Replace the rename step with a tar step**

Find this step:
```yaml
      - name: Rename binary
        run: mv dist/lazypr dist/${{ matrix.artifact_name }}
```

Replace with:
```yaml
      - name: Package binary
        run: tar -czf dist/${{ matrix.artifact_name }}.tar.gz -C dist lazypr
```

This creates a wrapped tarball: extracting it produces a `lazypr/` directory containing the bundle.

**Step 2: Update the upload artifact path**

Find:
```yaml
          path: dist/${{ matrix.artifact_name }}
```

Replace with:
```yaml
          path: dist/${{ matrix.artifact_name }}.tar.gz
```

**Step 3: Verify the release job**

The `release` job uses `dist/*` glob — no change needed there, it will pick up the `.tar.gz` files automatically.

**Step 4: Commit**

```bash
git add .github/workflows/release.yml
git commit -m "ci: package onedir bundle as tarball for release"
```

---

### Task 3: Update install.sh

**Files:**
- Modify: `scripts/install.sh`

**Step 1: Read the current install.sh**

Current relevant lines:
```bash
BINARY_URL="https://github.com/$REPO/releases/download/$VERSION/lazypr-$PLATFORM"
...
mkdir -p "$INSTALL_DIR"
curl -fsSL "$BINARY_URL" -o "$INSTALL_DIR/lazypr"
chmod +x "$INSTALL_DIR/lazypr"
```

**Step 2: Rewrite the download/install section**

Replace the `BINARY_URL` line and the download/install block with:

```bash
TARBALL_URL="https://github.com/$REPO/releases/download/$VERSION/lazypr-$PLATFORM.tar.gz"
SHARE_DIR="${LAZYPR_SHARE_DIR:-$HOME/.local/share}"

echo "Installing lazypr $VERSION for $PLATFORM..."

# Remove existing bundle if present (clean upgrade)
rm -rf "$SHARE_DIR/lazypr"

mkdir -p "$SHARE_DIR"
curl -fsSL "$TARBALL_URL" | tar -xz -C "$SHARE_DIR"

mkdir -p "$INSTALL_DIR"
ln -sf "$SHARE_DIR/lazypr/lazypr" "$INSTALL_DIR/lazypr"

echo "Installed: $INSTALL_DIR/lazypr -> $SHARE_DIR/lazypr/lazypr"
```

**Step 3: Verify the PATH hint still works**

The PATH check at the bottom uses `$INSTALL_DIR` — no change needed.

**Step 4: Commit**

```bash
git add scripts/install.sh
git commit -m "feat: update install script for onedir tarball distribution"
```

---

### Task 4: Update uninstall.sh

**Files:**
- Modify: `scripts/uninstall.sh`

**Step 1: Add removal of the bundle directory**

The uninstall script currently removes `~/.local/bin/lazypr` (the binary). With onedir, that's now a symlink and the actual bundle lives at `~/.local/share/lazypr/`.

Find:
```bash
# Remove binary installed via install.sh
if [[ -f "$BINARY" ]]; then
    rm -f "$BINARY"
    echo "Removed: $BINARY"
    removed=1
fi
```

Replace with:
```bash
SHARE_DIR="${LAZYPR_SHARE_DIR:-$HOME/.local/share}"
BUNDLE_DIR="$SHARE_DIR/lazypr"

# Remove binary/symlink and bundle dir installed via install.sh
if [[ -L "$BINARY" || -f "$BINARY" ]]; then
    rm -f "$BINARY"
    echo "Removed: $BINARY"
    removed=1
fi

if [[ -d "$BUNDLE_DIR" ]]; then
    rm -rf "$BUNDLE_DIR"
    echo "Removed: $BUNDLE_DIR"
    removed=1
fi
```

Note: `-L` checks for symlink, `-f` keeps backward compatibility with old single-binary installs.

**Step 2: Commit**

```bash
git add scripts/uninstall.sh
git commit -m "fix: update uninstall script to remove onedir bundle"
```

---

### Task 5: Manual verification

No automated tests exist for shell scripts. Verify manually:

**Step 1: Build locally**

```bash
pip install -e . pyinstaller
pyinstaller lazypr.spec --distpath dist --noconfirm
```

Expected: `dist/lazypr/` directory created (not a single file). It should contain `lazypr` executable and `_internal/` subdirectory.

**Step 2: Test the binary directly**

```bash
./dist/lazypr --help
```

Expected: help output with no `RequestsDependencyWarning`.

**Step 3: Simulate install**

```bash
mkdir -p /tmp/test-lazypr-install/share /tmp/test-lazypr-install/bin
tar -czf /tmp/lazypr-test.tar.gz -C dist lazypr
tar -xz -C /tmp/test-lazypr-install/share < /tmp/lazypr-test.tar.gz
ln -sf /tmp/test-lazypr-install/share/lazypr/lazypr /tmp/test-lazypr-install/bin/lazypr
/tmp/test-lazypr-install/bin/lazypr --help
```

Expected: help output works via the symlink, no warnings.

**Step 4: Simulate uninstall**

```bash
rm -f /tmp/test-lazypr-install/bin/lazypr
rm -rf /tmp/test-lazypr-install/share/lazypr
```

Expected: both removed cleanly.
