#!/usr/bin/env bash
set -euo pipefail

OS="$(uname -s)"

install_pip_package() {
    local package="$1" binary="${2:-$1}"
    if command -v "$binary" >/dev/null 2>&1; then
        echo "$binary already installed"
        return
    fi
    if ! command -v pip3 >/dev/null 2>&1; then
        echo "SKIP: pip3 not found. Install Python 3 first: https://www.python.org/" >&2
        return 0
    fi
    echo "Installing $package..."
    pip3 install --quiet "$package"
}

install_flake8() {
    install_pip_package flake8
}

install_yamllint() {
    install_pip_package yamllint
}

install_npm_package() {
    local package="$1" binary="$2"
    if command -v "$binary" >/dev/null 2>&1; then
        echo "$binary already installed"
        return
    fi
    if ! command -v npm >/dev/null 2>&1; then
        echo "SKIP: npm not found. Install Node.js first: https://nodejs.org/" >&2
        return 0
    fi
    echo "Installing $package..."
    npm install -g "$package" --quiet
}

install_tsc() {
    install_npm_package typescript tsc
}

install_markdownlint() {
    install_npm_package markdownlint-cli markdownlint
}

install_go() {
    if command -v go >/dev/null 2>&1; then
        echo "go already installed"
        return
    fi
    case "$OS" in
        Darwin)
            if command -v brew >/dev/null 2>&1; then
                echo "Installing go via Homebrew..."
                brew install go
            else
                echo "SKIP: Homebrew not found. Install from https://brew.sh/ or Go from https://go.dev/dl/" >&2
                return 0
            fi
            ;;
        Linux)
            if command -v apt-get >/dev/null 2>&1; then
                echo "Installing go via apt..."
                sudo apt-get install -y golang-go
            elif command -v yum >/dev/null 2>&1; then
                echo "Installing go via yum..."
                sudo yum install -y golang
            else
                echo "SKIP: No supported package manager found. Install Go from https://go.dev/dl/" >&2
                return 0
            fi
            ;;
        *)
            echo "SKIP: Unsupported OS: $OS. Install Go from https://go.dev/dl/" >&2
            return 0
            ;;
    esac
}

verify_tools() {
    echo ""
    echo "Tool versions:"
    flake8 --version       2>/dev/null || echo "flake8: not available"
    yamllint --version     2>/dev/null || echo "yamllint: not available"
    tsc --version          2>/dev/null || echo "tsc: not available"
    markdownlint --version 2>/dev/null || echo "markdownlint: not available"
    go version             2>/dev/null || echo "go: not available"
}

main() {
    echo "Setting up ai-developer-kit static analysis tools (OS: $OS)"
    echo ""
    install_flake8
    install_yamllint
    install_tsc
    install_markdownlint
    install_go
    verify_tools
    echo ""
    echo "Setup complete."
}

main
