#!/usr/bin/env bash
# Run static analysis on changed files. Add new extensions by appending a block below.
set -uo pipefail

changed_files="${*:-$(git diff --name-only main...HEAD 2>/dev/null)}"

if [ -z "$changed_files" ]; then
    echo "No changed files detected."
    exit 0
fi

exit_code=0

require_tool() {
    local tool="$1"
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "ERROR: $tool not installed. Run ./setup.sh to install required tools." >&2
        exit_code=1
        return 1
    fi
    return 0
}

py_files=()
ts_files=()
md_files=()
json_files=()
yaml_files=()
has_go=false

while IFS= read -r file; do
    [ -f "$file" ] || continue
    case "$file" in
        *.py)           py_files+=("$file") ;;
        *.ts|*.tsx)     ts_files+=("$file") ;;
        *.md)           md_files+=("$file") ;;
        *.json)         json_files+=("$file") ;;
        *.yml|*.yaml)   yaml_files+=("$file") ;;
        *.go)           has_go=true ;;
    esac
done <<< "$changed_files"

if [ ${#py_files[@]} -gt 0 ] && require_tool flake8; then
    flake8 "${py_files[@]}" || exit_code=1
fi

if [ ${#ts_files[@]} -gt 0 ] && require_tool tsc; then
    tsc --noEmit || exit_code=1
fi

if [ "$has_go" = true ] && require_tool go; then
    go vet ./... || exit_code=1
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
