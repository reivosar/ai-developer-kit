#!/usr/bin/env bash
# Install the external tools the kit's hooks call: linters and test tools for
# Python, Go, TypeScript, Rust, Java, and Kotlin, and the package managers
# they need.
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
KIT_TOOLS="$KIT_TOOLS checkstyle detekt"
OS="$(uname -s)"
# The Rust, Go, ESLint, and jar installers.
HOOKS_DIR="."
case "${BASH_SOURCE[0]}" in */*) HOOKS_DIR="${BASH_SOURCE[0]%/*}" ;; esac
# shellcheck source=install-lint-tools.sh
source "$HOOKS_DIR/install-lint-tools.sh"
# The Homebrew, apt, yum, pipx, npm, and pip installers.
# shellcheck source=install-packages.sh
source "$HOOKS_DIR/install-packages.sh"
# pipx, pip --user, and go install (GOBIN below) put commands in ~/.local/bin,
# which the shell that started this script may not have on PATH.
[ -n "${HOME:-}" ] && PATH="$PATH:$HOME/.local/bin"

#######################################
# Tell whether a command is on PATH.
# Arguments:
#   The command's name.
# Returns:
#   0 when it is, 1 otherwise.
#######################################
has_command() {
    command -v "$1" >/dev/null 2>&1
}

#######################################
# Tell whether a name is one of the kit's tools.
# Globals:
#   KIT_TOOLS
# Arguments:
#   The name.
# Returns:
#   0 when it is, 1 otherwise.
#######################################
is_kit_tool() {
    case " $KIT_TOOLS " in
        *" $1 "*) return 0 ;;
    esac
    return 1
}

#######################################
# Tell whether a kit tool is present. pytest-cov has no command of its own;
# pytest gains its options.
# Arguments:
#   The tool's kit name.
# Returns:
#   0 when it is present, 1 otherwise.
#######################################
is_installed() {
    if [ "$1" = pytest-cov ]; then
        [[ "$(pytest --help 2>/dev/null)" == *--cov-branch* ]]
        return
    fi
    case "$1" in
        eslint-jsdoc | checkstyle | detekt) is_lint_tool_installed "$1" ;;
        *) has_command "$1" ;;
    esac
}

#######################################
# Install one kit tool with whichever installer it needs.
# Arguments:
#   The tool's kit name.
# Returns:
#   Non-zero when the installer fails.
#######################################
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
        eslint-jsdoc) install_eslint_jsdoc ;;
        checkstyle | detekt) install_jar "$1" ;;
        cargo-clippy) install_clippy ;;
        cargo-llvm-cov) install_llvm_cov ;;
    esac
}

#######################################
# Install a kit tool unless it is present, and check it is present after.
# Arguments:
#   The tool's kit name.
# Outputs:
#   Progress and errors, to stderr, with the installer's own output.
# Returns:
#   1 when the tool could not be installed or is still not found.
#######################################
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

#######################################
# End the script with 2 when a name is not one of the kit's tools, before
# anything is installed.
# Globals:
#   KIT_TOOLS
# Arguments:
#   The names asked for.
# Outputs:
#   The unknown name and the known ones, to stderr.
# Returns:
#   Exits 2 on an unknown name.
#######################################
reject_unknown_tools() {
    local tool
    for tool in "$@"; do
        is_kit_tool "$tool" && continue
        echo "ERROR: $tool is not a tool this kit installs. Known: $KIT_TOOLS" >&2
        exit 2
    done
}

#######################################
# Install each named tool that is missing, or list the names accepted.
# Globals:
#   KIT_TOOLS
# Arguments:
#   Tool names, or --list.
# Outputs:
#   The names with --list, to stdout; usage and errors, to stderr.
# Returns:
#   Exits 0 when every tool is there, 1 when one could not be installed,
#   and 2 on a usage error or an unknown name.
#######################################
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
