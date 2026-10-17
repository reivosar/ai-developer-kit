#!/usr/bin/env bash
# Installers for the linters that are not a plain package: the Rust and Go
# tools, ESLint with eslint-plugin-jsdoc, and the Checkstyle and detekt jars.
# install-tool.sh sources this file and provides has_command, ensure_tool, OS.

case "${BASH_SOURCE[0]}" in
    */*) LINT_HOME="${BASH_SOURCE[0]%/*}/lint-config" ;;
    *) LINT_HOME="lint-config" ;;
esac
# ESLint and the plugin go where lint-config/eslint-jsdoc.config.mjs loads
# them from; the jars go next to the kit's Checkstyle and detekt configs.
LINT_NODE_PREFIX="${LINT_NODE_PREFIX:-$LINT_HOME}"
LINT_JAR_DIR="${LINT_JAR_DIR:-$LINT_HOME/jars}"
ESLINT_JSDOC_PACKAGES="eslint@9 eslint-plugin-jsdoc typescript-eslint"
CHECKSTYLE_JAR_URL="https://github.com/checkstyle/checkstyle/releases/download/checkstyle-14.3.0/checkstyle-14.3.0-all.jar"
DETEKT_JAR_URL="https://github.com/detekt/detekt/releases/download/v1.23.8/detekt-cli-1.23.8-all.jar"

#######################################
# Tell whether a linter installed outside PATH is present.
# Globals:
#   LINT_NODE_PREFIX, LINT_JAR_DIR
# Arguments:
#   The tool's kit name: eslint-jsdoc, checkstyle, or detekt.
# Returns:
#   0 when it is present, 1 otherwise.
#######################################
is_lint_tool_installed() {
    case "$1" in
        eslint-jsdoc) [ -x "$LINT_NODE_PREFIX/node_modules/.bin/eslint" ] \
            && [ -d "$LINT_NODE_PREFIX/node_modules/eslint-plugin-jsdoc" ] ;;
        *) [ -f "$LINT_JAR_DIR/$1.jar" ] ;;
    esac
}

#######################################
# Install clippy. Rust itself comes from rustup, which is not installed here.
# Returns:
#   Non-zero when rustup is missing or fails.
#######################################
install_clippy() {
    has_command rustup && rustup component add clippy
}

#######################################
# Install cargo-llvm-cov, or the release the toolchain can build when the
# newest one needs a newer rustc; cargo names that release in its error.
# Outputs:
#   cargo's output of a failed install, to stdout.
# Returns:
#   Non-zero when rustup is missing or no release can be built.
#######################################
install_llvm_cov() {
    has_command rustup && rustup component add llvm-tools-preview || return 1
    local output older='`cargo-llvm-cov ([0-9.]+)` supports rustc'
    output=$(cargo install cargo-llvm-cov 2>&1) && return 0
    echo "$output"
    [[ "$output" =~ $older ]] || return 1
    cargo install cargo-llvm-cov --version "${BASH_REMATCH[1]}" --locked
}

#######################################
# Install revive with go into ~/.local/bin; go links it itself, so this needs
# no Xcode tools on macOS. Homebrew is used only on a Mac that has no go.
# Globals:
#   OS, HOME
# Returns:
#   Non-zero when neither go nor Homebrew can install it.
#######################################
install_revive() {
    if [ "$OS" = Darwin ] && ! has_command go; then
        has_command brew && brew install revive
        return
    fi
    ensure_tool go && GOBIN="${HOME:+$HOME/.local/bin}" \
        go install github.com/mgechev/revive@latest
}

#######################################
# Install ESLint and eslint-plugin-jsdoc into LINT_NODE_PREFIX.
# Globals:
#   LINT_NODE_PREFIX, ESLINT_JSDOC_PACKAGES
# Returns:
#   Non-zero when npm is missing or the install fails.
#######################################
install_eslint_jsdoc() {
    # shellcheck disable=SC2086
    ensure_tool npm && npm install --prefix "$LINT_NODE_PREFIX" --no-save $ESLINT_JSDOC_PACKAGES
}

#######################################
# Download a linter's jar into LINT_JAR_DIR. The download lands in a .part
# file first, so an interrupted one never passes for the jar.
# Globals:
#   LINT_JAR_DIR, CHECKSTYLE_JAR_URL, DETEKT_JAR_URL
# Arguments:
#   The tool's kit name: checkstyle or detekt.
# Outputs:
#   Why no jar was downloaded, to stderr.
# Returns:
#   Non-zero when java or curl is missing or the download fails.
#######################################
install_jar() {
    local url="$CHECKSTYLE_JAR_URL" jar="$LINT_JAR_DIR/$1.jar"
    [ "$1" = detekt ] && url="$DETEKT_JAR_URL"
    if ! has_command java; then
        echo "$1 needs a Java runtime; install a JDK first." >&2
        return 1
    fi
    has_command curl && mkdir -p "$LINT_JAR_DIR" \
        && curl -fsSL --retry 2 -o "$jar.part" "$url" && mv "$jar.part" "$jar"
}
