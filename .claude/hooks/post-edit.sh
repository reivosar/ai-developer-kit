#!/usr/bin/env bash
# Post-tool-call hook: auto-format files after Write or Edit
# Receives JSON on stdin: {"tool_name": "...", "tool_input": {"file_path": "..."}}

INPUT=$(cat)
FILE=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null)

if [ -z "$FILE" ] || [ ! -f "$FILE" ]; then
  exit 0
fi

EXT="${FILE##*.}"

run_fmt() {
  local label="$1"; shift
  "$@" 2>/dev/null || echo "WARNING: $label failed on $FILE" >&2
}

case "$EXT" in
  js|jsx|ts|tsx|json|css|md)
    if command -v prettier &>/dev/null; then
      run_fmt prettier prettier --write "$FILE" --loglevel silent
    fi
    ;;
  py)
    if command -v black &>/dev/null; then
      run_fmt black black "$FILE" -q
    elif command -v autopep8 &>/dev/null; then
      run_fmt autopep8 autopep8 --in-place "$FILE"
    fi
    ;;
  go)
    if command -v gofmt &>/dev/null; then
      run_fmt gofmt gofmt -w "$FILE"
    fi
    ;;
  rb)
    if command -v rubocop &>/dev/null; then
      run_fmt rubocop rubocop -a "$FILE" --no-color -q
    fi
    ;;
  sh|bash)
    if command -v shfmt &>/dev/null; then
      run_fmt shfmt shfmt -w "$FILE"
    fi
    ;;
esac

# The changed file is linted at once, so a finding is fixed while the change
# is fresh rather than at commit. Exit 2 hands the findings back to the agent.
HOOKS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Only the project's own files are held to its lint rules: a file elsewhere,
# such as a memory note, is left alone. Outside a git repository, every file is.
PROJECT_ROOT="$(git -C "$HOOKS_DIR" rev-parse --show-toplevel 2>/dev/null)"
case "$FILE" in
  /*) ABSOLUTE_FILE="$FILE" ;;
  *) ABSOLUTE_FILE="$PWD/$FILE" ;;
esac
if [ -n "$PROJECT_ROOT" ] && [[ "$ABSOLUTE_FILE" != "$PROJECT_ROOT"/* ]]; then
  exit 0
fi
if ! findings=$("$HOOKS_DIR/static-analysis.sh" "$FILE" 2>&1); then
  echo "BLOCKED: static analysis found problems in $FILE" >&2
  echo "$findings" >&2
  exit 2
fi

exit 0
