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

if [[ -z "$VERSION" ]]; then
    echo "Error: could not fetch latest version from GitHub" >&2
    exit 1
fi

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
