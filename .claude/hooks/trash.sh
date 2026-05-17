#!/usr/bin/env bash
# Move files to the session trash instead of deleting permanently

source "$(dirname "${BASH_SOURCE[0]}")/hook-lib.sh"
PROJECT_ROOT="$REPO_ROOT"

SESSION_KEY=$(printf '%s' "$PROJECT_ROOT" | md5)
SESSION_FILE="/tmp/claude-session-trash-dir-$SESSION_KEY"

if [ -s "$SESSION_FILE" ]; then
  TRASH_DIR="$(cat "$SESSION_FILE")"
else
  TIMESTAMP=$(python3 -c "from datetime import datetime; print(datetime.now().strftime('%Y-%m-%d_%H-%M-%S.') + f'{datetime.now().microsecond//1000:03d}')")
  TRASH_DIR="$PROJECT_ROOT/.trash/$TIMESTAMP"
  echo "$TRASH_DIR" > "$SESSION_FILE"
fi

mkdir -p "$TRASH_DIR"

for target in "$@"; do
  ABS_TARGET="$(cd "$(dirname "$target")" 2>/dev/null && pwd)/$(basename "$target")"
  if [[ "$ABS_TARGET" != "$PROJECT_ROOT/"* ]]; then
    echo "BLOCKED: $target is outside project root" >&2
    exit 2
  fi
  DEST="$TRASH_DIR/$(basename "$target")"
  if [ -e "$DEST" ]; then
    SUFFIX=$(python3 -c "from datetime import datetime; print(datetime.now().strftime('%H-%M-%S.') + f'{datetime.now().microsecond//1000:03d}')")
    DEST="${DEST}.${SUFFIX}"
  fi
  mv "$target" "$DEST"
done
