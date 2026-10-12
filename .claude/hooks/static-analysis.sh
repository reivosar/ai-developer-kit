#!/usr/bin/env bash
# Run static analysis on changed files. Add new extensions by appending a block below.
set -uo pipefail

if [ $# -gt 0 ]; then
    changed_files=$(printf '%s\n' "$@")
elif [ "${STATIC_ANALYSIS_MODE:-}" = "staged" ]; then
    changed_files=$(git diff --name-only --cached 2>/dev/null) || {
        echo "ERROR: git diff --cached failed (not a git repo?)" >&2
        exit 1
    }
else
    changed_files=$(git diff --name-only main...HEAD 2>/dev/null) || {
        echo "ERROR: git diff failed (not a git repo or branch 'main' not found)" >&2
        exit 1
    }
fi

if [ -z "$changed_files" ]; then
    echo "No changed files detected."
    exit 0
fi

exit_code=0

hooks_dir="."
case "${BASH_SOURCE[0]}" in
    */*) hooks_dir="${BASH_SOURCE[0]%/*}" ;;
esac
INSTALLER="$hooks_dir/install-tool.sh"

# A missing linter is installed, not skipped: a skipped linter reports nothing,
# which reads the same as a clean file.
require_tool() {
    local tool="$1"
    command -v "$tool" >/dev/null 2>&1 && return 0
    "$INSTALLER" "$tool" && return 0
    echo "ERROR: $tool is not installed and could not be installed." >&2
    exit_code=1
    return 1
}

py_files=()
ts_files=()
md_files=()
json_files=()
yaml_files=()
go_files=()
has_rust=false

while IFS= read -r file; do
    [ -f "$file" ] || continue
    case "$file" in
        *.py)           py_files+=("$file") ;;
        *.ts|*.tsx)     ts_files+=("$file") ;;
        *.md)           md_files+=("$file") ;;
        *.json)         json_files+=("$file") ;;
        *.yml|*.yaml)   yaml_files+=("$file") ;;
        *.go)           go_files+=("$file") ;;
        *.rs)           has_rust=true ;;
    esac
done <<< "$changed_files"

has_eslint_config() {
    local name
    for name in eslint.config.js eslint.config.mjs eslint.config.cjs \
        eslint.config.ts .eslintrc .eslintrc.js .eslintrc.cjs .eslintrc.json \
        .eslintrc.yml .eslintrc.yaml; do
        [ -f "$name" ] && return 0
    done
    return 1
}

# A project that configured ESLint is linted by its own rules. Any other
# project gets Biome, whose default rules need no configuration.
lint_typescript() {
    if has_eslint_config; then
        if require_tool npx; then
            npx --no-install eslint "$@" || exit_code=1
        fi
    elif require_tool biome; then
        biome lint "$@" || exit_code=1
    fi
}

check_go_format() {
    local unformatted
    unformatted=$(gofmt -l "$@")
    if [ -n "$unformatted" ]; then
        echo "gofmt: not formatted: $unformatted"
        exit_code=1
    fi
}

# Each language gets a check for errors and a check for style: flake8 does
# both for Python, tsc and a linter for TypeScript, go vet and gofmt for Go,
# and clippy with warnings denied for Rust.
if [ ${#py_files[@]} -gt 0 ] && require_tool flake8; then
    flake8 "${py_files[@]}" || exit_code=1
fi

if [ ${#ts_files[@]} -gt 0 ]; then
    if require_tool tsc; then
        tsc --noEmit || exit_code=1
    fi
    lint_typescript "${ts_files[@]}"
fi

if [ ${#go_files[@]} -gt 0 ] && require_tool go; then
    go vet ./... || exit_code=1
    if require_tool gofmt; then
        check_go_format "${go_files[@]}"
    fi
fi

if [ "$has_rust" = true ] && require_tool cargo && require_tool cargo-clippy; then
    cargo clippy --all-targets --quiet -- -D warnings || exit_code=1
fi

if [ ${#md_files[@]} -gt 0 ] && require_tool markdownlint; then
    markdownlint "${md_files[@]}" || exit_code=1
fi

if [ ${#json_files[@]} -gt 0 ] && require_tool python3; then
    for f in "${json_files[@]}"; do
        python3 -m json.tool "$f" > /dev/null || { echo "JSON error: $f"; exit_code=1; }
    done
fi

if [ ${#yaml_files[@]} -gt 0 ] && require_tool yamllint; then
    yamllint "${yaml_files[@]}" || exit_code=1
fi

exit "$exit_code"
