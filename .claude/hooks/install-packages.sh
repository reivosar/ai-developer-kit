#!/usr/bin/env bash
# Installers that go through a package manager: the system's (Homebrew, apt,
# yum), pipx, npm, and pip. install-tool.sh sources this file and provides
# has_command, ensure_tool, and OS.

#######################################
# Install packages with apt or yum. sudo -n fails at once when it would need
# a password no one can type.
# Arguments:
#   The apt package names, then the yum package names, each one word-split
#   string, so that "nodejs npm" is two packages.
# Returns:
#   1 when there is neither apt nor yum, or the install fails.
#######################################
install_linux_package() {
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

#######################################
# Install a package with the system's package manager.
# Globals:
#   OS
# Arguments:
#   The Homebrew formula, the apt package names, then the yum package names.
# Returns:
#   1 on a system with no supported package manager, or when it fails.
#######################################
install_system_package() {
    case "$OS" in
        Darwin) has_command brew && brew install "$1" ;;
        Linux) install_linux_package "$2" "$3" ;;
        *) return 1 ;;
    esac
}

#######################################
# Install pipx: with pip on a Linux without apt, else as a system package.
# Globals:
#   OS
#######################################
install_pipx() {
    if [ "$OS" = Linux ] && ! has_command apt-get; then
        pip3 install --user pipx
    else
        install_system_package pipx pipx pipx
    fi
}

#######################################
# Install a Python command with pipx, installing pipx first when needed.
# Arguments:
#   The package's name.
#######################################
install_with_pipx() {
    ensure_tool pipx && pipx install "$1"
}

#######################################
# Install a Node package globally with npm, installing npm first when needed.
# Arguments:
#   The package's name.
#######################################
install_with_npm() {
    ensure_tool npm && npm install -g "$1" --quiet
}

#######################################
# Install pytest or pytest-cov. Tests import the project's own packages, so
# inside a virtualenv they have to live in that virtualenv; outside one, pipx
# keeps the system Python as the operating system shipped it.
# Globals:
#   VIRTUAL_ENV
# Arguments:
#   pytest or pytest-cov.
#######################################
install_pytest_package() {
    if [ -n "${VIRTUAL_ENV:-}" ]; then
        python3 -m pip install "$1"
    elif [ "$1" = pytest ]; then
        install_with_pipx pytest
    else
        ensure_tool pytest && ensure_tool pipx && pipx inject pytest "$1"
    fi
}
