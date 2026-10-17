#!/usr/bin/env bash
set -euo pipefail

OS="$(uname -s)"

# install_runtime <command> <label> <url> <brew formula> <apt packages> <yum packages>
# installs a language runtime with the system's package manager, or names
# where to get it when there is none. A package list is one word-split string.
install_runtime() {
    local command="$1" label="$2" url="$3" formula="$4" apt_packages="$5" yum_packages="$6"
    case "$OS" in
        Darwin)
            if command -v brew >/dev/null 2>&1; then
                echo "Installing/upgrading $command via Homebrew..."
                brew upgrade "$formula" 2>/dev/null || brew install "$formula"
            else
                echo "SKIP: Homebrew not found. Install from https://brew.sh/ or $label from $url" >&2
            fi
            ;;
        Linux)
            if command -v apt-get >/dev/null 2>&1; then
                echo "Installing/upgrading $command via apt..."
                # shellcheck disable=SC2086
                sudo apt-get install -y $apt_packages
            elif command -v yum >/dev/null 2>&1; then
                echo "Installing/upgrading $command via yum..."
                # shellcheck disable=SC2086
                sudo yum install -y $yum_packages
            else
                echo "SKIP: No supported package manager found. Install $label from $url" >&2
            fi
            ;;
        *)
            echo "SKIP: Unsupported OS: $OS. Install $label from $url" >&2
            ;;
    esac
}

install_python3() {
    install_runtime python3 Python https://www.python.org/ python3 \
        "python3 python3-pip" "python3 python3-pip"
}

install_node() {
    install_runtime node Node.js https://nodejs.org/ node "nodejs npm" "nodejs npm"
}

install_go() {
    install_runtime go Go https://go.dev/dl/ go golang-go golang
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

# The installer holds the list of tools the hooks call, so a tool added there
# is installed here without this file naming it.
install_missing_kit_tools() {
    local kit_root="."
    case "$0" in
        */*) kit_root="${0%/*}" ;;
    esac
    local installer="$kit_root/.claude/hooks/install-tool.sh"
    echo "Installing the hook tools that are still missing..."
    # shellcheck disable=SC2046
    "$installer" $("$installer" --list) \
        || echo "WARNING: some hook tools could not be installed." >&2
}

verify_tools() {
    echo ""
    echo "Tool versions:"
    python3 --version      2>/dev/null || echo "python3: not available"
    pipx --version         2>/dev/null || echo "pipx: not available"
    flake8 --version       2>/dev/null || echo "flake8: not available"
    yamllint --version     2>/dev/null || echo "yamllint: not available"
    pytest --version       2>/dev/null || echo "pytest: not available"
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
    install_missing_kit_tools
    verify_tools
    echo ""
    echo "Setup complete."
}

main
