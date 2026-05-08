#!/usr/bin/env bash
# Create a session-scoped trash directory and record its path for trash.sh

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
TIMESTAMP=$(python3 -c "from datetime import datetime; print(datetime.now().strftime('%Y-%m-%d_%H-%M-%S.') + f'{datetime.now().microsecond//1000:03d}')")
TRASH_DIR="$PROJECT_ROOT/.trash/$TIMESTAMP"
mkdir -p "$TRASH_DIR"
echo "$TRASH_DIR" > /tmp/claude-session-trash-dir
