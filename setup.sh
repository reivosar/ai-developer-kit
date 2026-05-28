#!/usr/bin/env bash
set -euo pipefail

OS="$(uname -s)"

install_python3() {
    case "$OS" in
        Darwin)
            if command -v brew >/dev/null 2>&1; then
                echo "Installing/upgrading python3 via Homebrew..."
                brew upgrade python3 2>/dev/null || brew install python3
            else
                echo "SKIP: Homebrew not found. Install from https://brew.sh/ or Python from https://www.python.org/" >&2
            fi
            ;;
        Linux)
            if command -v apt-get >/dev/null 2>&1; then
                echo "Installing/upgrading python3 via apt..."
                sudo apt-get install -y python3 python3-pip
            elif command -v yum >/dev/null 2>&1; then
                echo "Installing/upgrading python3 via yum..."
                sudo yum install -y python3 python3-pip
            else
                echo "SKIP: No supported package manager found. Install Python from https://www.python.org/" >&2
            fi
            ;;
        *)
            echo "SKIP: Unsupported OS: $OS. Install Python from https://www.python.org/" >&2
            ;;
    esac
}

install_pipx() {
    case "$OS" in
        Darwin)
            if command -v brew >/dev/null 2>&1; then
                echo "Installing/upgrading pipx via Homebrew..."
                brew upgrade pipx 2>/dev/null || brew install pipx
            else
                echo "SKIP: Homebrew not found. Install pipx from https://pipx.pypa.io/" >&2
            fi
            ;;
        Linux)
            if command -v apt-get >/dev/null 2>&1; then
                echo "Installing/upgrading pipx via apt..."
                sudo apt-get install -y pipx
            elif command -v pip3 >/dev/null 2>&1; then
                echo "Installing pipx via pip3..."
                pip3 install --user --upgrade pipx
            else
                echo "SKIP: No supported package manager found. Install pipx from https://pipx.pypa.io/" >&2
            fi
            ;;
        *)
            echo "SKIP: Unsupported OS: $OS. Install pipx from https://pipx.pypa.io/" >&2
            ;;
    esac
}

install_pip_package() {
    local package="$1"
    if ! command -v pipx >/dev/null 2>&1; then
        echo "SKIP: pipx not found. Run setup.sh again after pipx is installed." >&2
        return 0
    fi
    echo "Installing/upgrading $package..."
    pipx install "$package" 2>/dev/null || pipx upgrade "$package"
}

install_flake8() {
    install_pip_package flake8
}

install_yamllint() {
    install_pip_package yamllint
}

install_npm_package() {
    local package="$1"
    if ! command -v npm >/dev/null 2>&1; then
        echo "SKIP: npm not found. Install Node.js first: https://nodejs.org/" >&2
        return 0
    fi
    echo "Installing/upgrading $package..."
    npm install -g "$package"@latest --quiet
}

install_tsc() {
    install_npm_package typescript
}

install_markdownlint() {
    install_npm_package markdownlint-cli
}

install_node() {
    case "$OS" in
        Darwin)
            if command -v brew >/dev/null 2>&1; then
                echo "Installing/upgrading node via Homebrew..."
                brew upgrade node 2>/dev/null || brew install node
            else
                echo "SKIP: Homebrew not found. Install from https://brew.sh/ or Node.js from https://nodejs.org/" >&2
            fi
            ;;
        Linux)
            if command -v apt-get >/dev/null 2>&1; then
                echo "Installing/upgrading node via apt..."
                sudo apt-get install -y nodejs npm
            elif command -v yum >/dev/null 2>&1; then
                echo "Installing/upgrading node via yum..."
                sudo yum install -y nodejs npm
            else
                echo "SKIP: No supported package manager found. Install Node.js from https://nodejs.org/" >&2
            fi
            ;;
        *)
            echo "SKIP: Unsupported OS: $OS. Install Node.js from https://nodejs.org/" >&2
            ;;
    esac
}

install_go() {
    case "$OS" in
        Darwin)
            if command -v brew >/dev/null 2>&1; then
                echo "Installing/upgrading go via Homebrew..."
                brew upgrade go 2>/dev/null || brew install go
            else
                echo "SKIP: Homebrew not found. Install from https://brew.sh/ or Go from https://go.dev/dl/" >&2
            fi
            ;;
        Linux)
            if command -v apt-get >/dev/null 2>&1; then
                echo "Installing/upgrading go via apt..."
                sudo apt-get install -y golang-go
            elif command -v yum >/dev/null 2>&1; then
                echo "Installing/upgrading go via yum..."
                sudo yum install -y golang
            else
                echo "SKIP: No supported package manager found. Install Go from https://go.dev/dl/" >&2
            fi
            ;;
        *)
            echo "SKIP: Unsupported OS: $OS. Install Go from https://go.dev/dl/" >&2
            ;;
    esac
}

verify_tools() {
    echo ""
    echo "Tool versions:"
    python3 --version      2>/dev/null || echo "python3: not available"
    pipx --version         2>/dev/null || echo "pipx: not available"
    flake8 --version       2>/dev/null || echo "flake8: not available"
    yamllint --version     2>/dev/null || echo "yamllint: not available"
    node --version         2>/dev/null || echo "node: not available"
    tsc --version          2>/dev/null || echo "tsc: not available"
    markdownlint --version 2>/dev/null || echo "markdownlint: not available"
    go version             2>/dev/null || echo "go: not available"
    echo ""
    if ! command -v pipx >/dev/null 2>&1; then
        echo "WARNING: pipx not found — flake8 and yamllint were not installed. Install pipx: https://pipx.pypa.io/" >&2
    fi
    if ! command -v npm >/dev/null 2>&1; then
        echo "WARNING: npm not found — tsc and markdownlint were not installed. Install Node.js: https://nodejs.org/" >&2
    fi
}

main() {
    echo "Setting up ai-developer-kit static analysis tools (OS: $OS)"
    echo ""
    install_python3
    install_pipx
    install_flake8
    install_yamllint
    install_node
    install_tsc
    install_markdownlint
    install_go
    verify_tools
    echo ""
    echo "Setup complete."
}

main
