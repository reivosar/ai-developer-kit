#!/usr/bin/env bash
# Install the external tools the kit's hooks call: linters and test tools for
# Python, Go, TypeScript, and Rust, and the package managers they need.
# Usage: install-tool.sh <tool>...   install each named tool that is missing
#        install-tool.sh --list      print the names this script accepts
#
# Only the names in KIT_TOOLS are accepted, and a tool that is already present
# is left alone. Formatters are absent on purpose: post-edit.sh runs whichever
# formatter a project has installed, so installing one here would start
# rewriting every file the project edits.
set -uo pipefail

KIT_TOOLS="pipx npm go flake8 yamllint pytest pytest-cov tsc markdownlint"
KIT_TOOLS="$KIT_TOOLS biome cargo-clippy cargo-llvm-cov pylint revive ruff eslint-jsdoc"
OS="$(uname -s)"
# eslint-jsdoc is ESLint with eslint-plugin-jsdoc, installed where the kit's
# lint-config/eslint-jsdoc.config.mjs loads the plugin from.
case "${BASH_SOURCE[0]}" in
    */*) LINT_NODE_PREFIX="${LINT_NODE_PREFIX:-${BASH_SOURCE[0]%/*}/lint-config}" ;;
    *) LINT_NODE_PREFIX="${LINT_NODE_PREFIX:-lint-config}" ;;
esac
ESLINT_JSDOC_PACKAGES="eslint@9 eslint-plugin-jsdoc typescript-eslint"
# pipx, pip --user, and go install (GOBIN below) put commands in ~/.local/bin,
# which the shell that started this script may not have on PATH.
[ -n "${HOME:-}" ] && PATH="$PATH:$HOME/.local/bin"

has_command() {
    command -v "$1" >/dev/null 2>&1
}

is_kit_tool() {
    case " $KIT_TOOLS " in
        *" $1 "*) return 0 ;;
    esac
    return 1
}

is_installed() {
    if [ "$1" = pytest-cov ]; then
        # pytest-cov has no command of its own; pytest gains its options.
        [[ "$(pytest --help 2>/dev/null)" == *--cov-branch* ]]
        return
    fi
    if [ "$1" = eslint-jsdoc ]; then
        [ -x "$LINT_NODE_PREFIX/node_modules/.bin/eslint" ] \
            && [ -d "$LINT_NODE_PREFIX/node_modules/eslint-plugin-jsdoc" ]
        return
    fi
    has_command "$1"
}

# Arguments: the apt package names, then the yum package names.
install_linux_package() {
    # sudo -n fails at once when it would need a password no one can type.
    # The names are left unquoted so that "nodejs npm" becomes two packages.
    if has_command apt-get; then
        # shellcheck disable=SC2086
        sudo -n apt-get install -y $1
    elif has_command yum; then
        # shellcheck disable=SC2086
        sudo -n yum install -y $2
    else
        return 1
    fi
}

# Arguments: the Homebrew formula, the apt package names, the yum package names.
install_system_package() {
    case "$OS" in
        Darwin) has_command brew && brew install "$1" ;;
        Linux) install_linux_package "$2" "$3" ;;
        *) return 1 ;;
    esac
}

install_pipx() {
    if [ "$OS" = Linux ] && ! has_command apt-get; then
        pip3 install --user pipx
    else
        install_system_package pipx pipx pipx
    fi
}

install_with_pipx() {
    ensure_tool pipx && pipx install "$1"
}

install_with_npm() {
    ensure_tool npm && npm install -g "$1" --quiet
}

# Tests import the project's own packages, so inside a virtualenv pytest has
# to live in that virtualenv. Outside one, pipx keeps the system Python as the
# operating system shipped it.
install_pytest_package() {
    if [ -n "${VIRTUAL_ENV:-}" ]; then
        python3 -m pip install "$1"
    elif [ "$1" = pytest ]; then
        install_with_pipx pytest
    else
        ensure_tool pytest && ensure_tool pipx && pipx inject pytest "$1"
    fi
}

# Rust itself comes from rustup, which this script does not install: without
# rustup these fail, and the caller reports the missing tool.
install_clippy() {
    has_command rustup && rustup component add clippy
}

install_llvm_cov() {
    has_command rustup && rustup component add llvm-tools-preview || return 1
    local output older='`cargo-llvm-cov ([0-9.]+)` supports rustc'
    output=$(cargo install cargo-llvm-cov 2>&1) && return 0
    echo "$output"
    # A toolchain too old for the newest release is told by cargo which
    # release it can build; that release is installed with its locked
    # dependencies, which were chosen for the same toolchain.
    [[ "$output" =~ $older ]] || return 1
    cargo install cargo-llvm-cov --version "${BASH_REMATCH[1]}" --locked
}

# revive is built with go into ~/.local/bin, the directory pipx also installs
# into. go links it itself, so this needs no Xcode tools on macOS; Homebrew is
# used only on a Mac that has no go.
install_revive() {
    if [ "$OS" = Darwin ] && ! has_command go; then
        has_command brew && brew install revive
        return
    fi
    # Without HOME, go puts it in its own default directory.
    ensure_tool go && GOBIN="${HOME:+$HOME/.local/bin}" \
        go install github.com/mgechev/revive@latest
}

install_tool() {
    case "$1" in
        pipx) install_pipx ;;
        npm) install_system_package node "nodejs npm" "nodejs npm" ;;
        go) install_system_package go golang-go golang ;;
        flake8 | yamllint | pylint | ruff) install_with_pipx "$1" ;;
        revive) install_revive ;;
        pytest | pytest-cov) install_pytest_package "$1" ;;
        tsc) install_with_npm typescript ;;
        markdownlint) install_with_npm markdownlint-cli ;;
        biome) install_with_npm @biomejs/biome ;;
        # shellcheck disable=SC2086
        eslint-jsdoc) ensure_tool npm \
            && npm install --prefix "$LINT_NODE_PREFIX" --no-save $ESLINT_JSDOC_PACKAGES ;;
        cargo-clippy) install_clippy ;;
        cargo-llvm-cov) install_llvm_cov ;;
    esac
}

ensure_tool() {
    is_installed "$1" && return 0
    echo "Installing $1..." >&2
    if ! install_tool "$1" >&2; then
        echo "ERROR: could not install $1." >&2
        return 1
    fi
    if ! is_installed "$1"; then
        echo "ERROR: $1 was installed but is not on PATH." >&2
        return 1
    fi
}

reject_unknown_tools() {
    local tool
    for tool in "$@"; do
        is_kit_tool "$tool" && continue
        echo "ERROR: $tool is not a tool this kit installs. Known: $KIT_TOOLS" >&2
        exit 2
    done
}

main() {
    if [ $# -eq 0 ]; then
        echo "Usage: install-tool.sh <tool>... | --list" >&2
        exit 2
    fi
    if [ "$1" = --list ]; then
        # shellcheck disable=SC2086
        printf '%s\n' $KIT_TOOLS
        exit 0
    fi
    reject_unknown_tools "$@"
    local tool status=0
    for tool in "$@"; do
        ensure_tool "$tool" || status=1
    done
    exit "$status"
}

main "$@"
