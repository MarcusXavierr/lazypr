#!/usr/bin/env bash

# GitHub CLI (gh) Installer Script
# Supports: macOS, Ubuntu/Debian, Fedora/RHEL/CentOS, Alpine, Arch Linux
# Can be run via: curl -fsSL https://raw.githubusercontent.com/MarcusXavierr/lazypr/main/setup.sh | bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if gh is already installed
check_existing() {
    if command -v gh &> /dev/null; then
        log_success "GitHub CLI (gh) is already installed: $(gh --version | head -n1)"
        prompt_auth
        exit 0
    fi
}

# Detect operating system
detect_os() {
    local os=""
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        os="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        os="macos"
    elif [[ "$OSTYPE" == "linux-musl"* ]] || [[ -f "/etc/alpine-release" ]]; then
        os="alpine"
    else
        log_error "Unsupported operating system: $OSTYPE"
        exit 1
    fi
    echo "$os"
}

# Detect Linux distribution
detect_distro() {
    if [[ -f "/etc/os-release" ]]; then
        . /etc/os-release
        echo "$ID"
    else
        echo "unknown"
    fi
}

# Install on macOS using Homebrew or direct download
install_macos() {
    log_info "Detected macOS"

    if command -v brew &> /dev/null; then
        log_info "Installing gh via Homebrew..."
        brew install gh
    else
        log_warning "Homebrew not found. Installing gh from GitHub release..."
        local arch
        arch=$(uname -m)
        local download_url

        if [[ "$arch" == "arm64" ]]; then
            download_url="https://github.com/cli/cli/releases/latest/download/gh_${version}_macOS_arm64.tar.gz"
        else
            download_url="https://github.com/cli/cli/releases/latest/download/gh_${version}_macOS_amd64.tar.gz"
        fi

        curl -fsSL "$download_url" -o /tmp/gh.tar.gz
        tar -xzf /tmp/gh.tar.gz -C /tmp
        sudo mv "/tmp/gh_${version}_macOS_"*/bin/gh /usr/local/bin/
        rm -rf /tmp/gh.tar.gz /tmp/gh_*
    fi
}

# Install on Ubuntu/Debian
install_debian() {
    log_info "Detected Debian/Ubuntu"
    log_info "Installing gh via apt..."

    # Install prerequisites
    sudo apt-get update
    sudo apt-get install -y curl gnupg

    # Add GitHub CLI repository
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
    sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null

    # Install gh
    sudo apt-get update
    sudo apt-get install -y gh
}

# Install on Fedora/RHEL/CentOS
install_fedora() {
    log_info "Detected Fedora/RHEL/CentOS"
    log_info "Installing gh via dnf/yum..."

    if command -v dnf &> /dev/null; then
        sudo dnf install -y 'dnf-command(config-manager)'
        sudo dnf config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo
        sudo dnf install -y gh
    elif command -v yum &> /dev/null; then
        sudo yum install -y yum-utils
        sudo yum-config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo
        sudo yum install -y gh
    else
        log_error "Neither dnf nor yum found. Falling back to manual installation."
        install_generic_linux
    fi
}

# Install on Alpine Linux
install_alpine() {
    log_info "Detected Alpine Linux"
    log_info "Installing gh via apk..."
    apk add --no-cache github-cli
}

# Install on Arch Linux
install_arch() {
    log_info "Detected Arch Linux"
    log_info "Installing gh via pacman..."
    sudo pacman -S --noconfirm github-cli
}

# Generic Linux installation from GitHub releases
install_generic_linux() {
    log_info "Installing gh from GitHub release..."

    local arch
    arch=$(uname -m)
    local download_arch

    case "$arch" in
        x86_64)
            download_arch="amd64"
            ;;
        aarch64|arm64)
            download_arch="arm64"
            ;;
        i386|i686)
            download_arch="386"
            ;;
        armv7l)
            download_arch="armv6"
            ;;
        *)
            log_error "Unsupported architecture: $arch"
            exit 1
            ;;
    esac

    local download_url="https://github.com/cli/cli/releases/latest/download/gh_${version}_linux_${download_arch}.tar.gz"

    log_info "Downloading from $download_url"
    curl -fsSL "$download_url" -o /tmp/gh.tar.gz
    tar -xzf /tmp/gh.tar.gz -C /tmp
    sudo mv "/tmp/gh_${version}_linux_${download_arch}/bin/gh" /usr/local/bin/
    sudo mv "/tmp/gh_${version}_linux_${download_arch}/share"/* /usr/local/share/
    rm -rf /tmp/gh.tar.gz "/tmp/gh_${version}_linux_${download_arch}"
}

# Get the latest version number
get_latest_version() {
    curl -fsSL "https://api.github.com/repos/cli/cli/releases/latest" | grep -o '"tag_name": "[^"]*' | cut -d'"' -f4 | sed 's/^v//'
}

# Prompt user to run gh auth login
prompt_auth() {
    echo ""
    log_info "GitHub CLI requires authentication to create PRs."

    # Check if we're in a non-interactive environment
    if [[ ! -t 0 ]]; then
        log_warning "Non-interactive environment detected. Please run 'gh auth login' manually."
        return
    fi

    read -p "Would you like to run 'gh auth login' now? [Y/n] " response
    response=${response:-Y}

    if [[ "$response" =~ ^[Yy]$ ]]; then
        log_info "Starting GitHub authentication..."
        gh auth login
        log_success "Authentication complete!"
    else
        log_info "Skipping authentication. You can run 'gh auth login' later when ready."
    fi
}

# Main installation logic
main() {
    echo "========================================"
    echo "  GitHub CLI (gh) Installer"
    echo "========================================"
    echo ""

    # Check if already installed
    check_existing

    # Get the latest version
    log_info "Fetching latest version..."
    version=$(get_latest_version)
    log_info "Latest version: $version"

    # Detect OS and install
    local os
    os=$(detect_os)

    case "$os" in
        macos)
            install_macos
            ;;
        linux)
            local distro
            distro=$(detect_distro)
            log_info "Detected distribution: $distro"

            case "$distro" in
                ubuntu|debian)
                    install_debian
                    ;;
                fedora|rhel|centos|rocky|almalinux)
                    install_fedora
                    ;;
                arch|manjaro)
                    install_arch
                    ;;
                *)
                    log_warning "Unknown distribution. Trying generic Linux installation..."
                    install_generic_linux
                    ;;
            esac
            ;;
        alpine)
            install_alpine
            ;;
        *)
            log_error "Unsupported operating system: $os"
            exit 1
            ;;
    esac

    # Verify installation
    echo ""
    if command -v gh &> /dev/null; then
        log_success "GitHub CLI installed successfully!"
        gh --version
        prompt_auth
    else
        log_error "Installation failed. Please check the error messages above."
        exit 1
    fi
}

# Run main function
main
