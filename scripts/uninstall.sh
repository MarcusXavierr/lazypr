#!/usr/bin/env bash
set -e

INSTALL_DIR="${LAZYPR_INSTALL_DIR:-$HOME/.local/bin}"
BINARY="$INSTALL_DIR/lazypr"

removed=0

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

# Remove if installed via pip
if command -v pip &>/dev/null && pip show lazypr &>/dev/null 2>&1; then
    pip uninstall -y lazypr
    echo "Uninstalled lazypr via pip"
    removed=1
fi

# Remove config files if present
if [[ -f "$HOME/.lazypr" ]]; then
    rm -f "$HOME/.lazypr"
    echo "Removed: $HOME/.lazypr"
fi

if [[ -d "$HOME/.config/lazypr" ]]; then
    rm -rf "$HOME/.config/lazypr"
    echo "Removed: $HOME/.config/lazypr"
fi

if [[ $removed -eq 0 ]]; then
    echo "lazypr is not installed — nothing to remove."
else
    echo "lazypr uninstalled successfully."
fi
