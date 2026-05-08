#!/usr/bin/env bash
# Move files to the session trash instead of deleting permanently

SESSION_FILE="/tmp/claude-session-trash-dir"

if [ -f "$SESSION_FILE" ]; then
  TRASH_DIR="$(cat "$SESSION_FILE")"
else
  PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
  TIMESTAMP=$(python3 -c "from datetime import datetime; print(datetime.now().strftime('%Y-%m-%d_%H-%M-%S.') + f'{datetime.now().microsecond//1000:03d}')")
  TRASH_DIR="$PROJECT_ROOT/.trash/$TIMESTAMP"
  echo "$TRASH_DIR" > "$SESSION_FILE"
fi

mkdir -p "$TRASH_DIR"

for target in "$@"; do
  mv "$target" "$TRASH_DIR/"
done
