#!/usr/bin/env python3
"""PreToolUse hook: block all Write/Edit on files outside a worktree."""
import json
import os
import sys
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hook_lib import WORKTREES_DIR  # noqa: E402


def is_in_worktree(path: str) -> bool:
    abs_path = Path(path).resolve()
    return str(abs_path).startswith(str(WORKTREES_DIR) + os.sep)


def main() -> None:
    data = json.load(sys.stdin)
    file_path: str = data.get("tool_input", {}).get("file_path", "")

    if not file_path:
        sys.exit(0)
    if is_in_worktree(file_path):
        sys.exit(0)

    print(f"BLOCKED: '{os.path.basename(file_path)}' must be edited inside a worktree.", file=sys.stderr)
    print("  Run /worktree to create one, then work inside .claude/worktrees/<name>/", file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
