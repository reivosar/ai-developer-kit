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
# The installer puts linters in ~/.local/bin; the caller's PATH may lack it.
[ -n "${HOME:-}" ] && PATH="$PATH:$HOME/.local/bin"
# Linter settings the kit adds: a code file holds at most 200 lines.
LINT_CONFIG="$hooks_dir/lint-config"
MAX_FILE_LINES=200

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
rs_files=()
sh_files=()

while IFS= read -r file; do
    [ -f "$file" ] || continue
    case "$file" in
        *.py)           py_files+=("$file") ;;
        *.ts|*.tsx)     ts_files+=("$file") ;;
        *.md)           md_files+=("$file") ;;
        *.json)         json_files+=("$file") ;;
        *.yml|*.yaml)   yaml_files+=("$file") ;;
        *.go)           go_files+=("$file") ;;
        *.rs)           rs_files+=("$file") ;;
        *.sh|*.bash)    sh_files+=("$file") ;;
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

has_biome_config() {
    [ -f biome.json ] || [ -f biome.jsonc ]
}

# A project that configured ESLint is linted by its own rules plus max-lines.
# Any other project gets Biome: with its own configuration when it has one,
# otherwise with the kit's, which adds the file length rule to the defaults.
lint_typescript() {
    if has_eslint_config; then
        if require_tool npx; then
            npx --no-install eslint --rule "max-lines: [error, $MAX_FILE_LINES]" "$@" \
                || exit_code=1
        fi
    elif require_tool biome; then
        if has_biome_config; then
            biome lint "$@" || exit_code=1
        else
            biome lint --config-path "$LINT_CONFIG" "$@" || exit_code=1
        fi
    fi
}

# check_projects: go vet, tsc, and clippy, each in the file's own project.
# shellcheck source=project-checks.sh
source "$hooks_dir/project-checks.sh"

# Clippy and the shell have no rule for file length, so the lines are counted
# here; a last line without a newline counts too.
check_file_length() {
    local file line count
    for file in "$@"; do
        count=0
        while IFS= read -r line || [ -n "$line" ]; do
            count=$((count + 1))
        done < "$file"
        if [ "$count" -gt "$MAX_FILE_LINES" ]; then
            echo "$file: $count lines, more than $MAX_FILE_LINES"
            exit_code=1
        fi
    done
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

# flake8 has no file length check; pylint's too-many-lines is the one used.
if [ ${#py_files[@]} -gt 0 ] && require_tool pylint; then
    pylint --disable=all --enable=too-many-lines --max-module-lines="$MAX_FILE_LINES" \
        --score=n "${py_files[@]}" || exit_code=1
fi

if [ ${#ts_files[@]} -gt 0 ]; then
    if require_tool tsc; then
        check_projects tsconfig.json "${ts_files[@]}"
    fi
    lint_typescript "${ts_files[@]}"
fi

if [ ${#go_files[@]} -gt 0 ] && require_tool go; then
    check_projects go.mod "${go_files[@]}"
    if require_tool gofmt; then
        check_go_format "${go_files[@]}"
    fi
    if require_tool revive; then
        revive -config "$LINT_CONFIG/revive.toml" -set_exit_status "${go_files[@]}" \
            || exit_code=1
    fi
fi

if [ ${#rs_files[@]} -gt 0 ]; then
    check_file_length "${rs_files[@]}"
    if require_tool cargo && require_tool cargo-clippy; then
        check_projects Cargo.toml "${rs_files[@]}"
    fi
fi

if [ ${#sh_files[@]} -gt 0 ]; then
    check_file_length "${sh_files[@]}"
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
