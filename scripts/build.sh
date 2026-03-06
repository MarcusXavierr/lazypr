#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "Installing dependencies..."
pip install -e . pyinstaller -q

echo "Building lazypr binary..."
pyinstaller lazypr.spec --distpath dist --noconfirm

echo ""
echo "Build complete: dist/lazypr"
echo "Testing binary..."
./dist/lazypr --help
