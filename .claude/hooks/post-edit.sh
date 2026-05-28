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

exit 0
