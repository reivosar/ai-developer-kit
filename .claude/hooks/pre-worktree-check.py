#!/usr/bin/env python3
"""PreToolUse hook: block Edit/Write on impl files outside a worktree."""
import json
import os
import sys

IMPL_EXTS = {
    ".ts", ".tsx", ".js", ".jsx", ".mts", ".mjs",
    ".py", ".go", ".java", ".rb", ".rs",
    ".kt", ".kts", ".swift", ".cs",
    ".cpp", ".cc", ".cxx", ".c", ".h", ".hpp", ".php",
}

KIT_BASENAMES = {"CLAUDE.md", "MEMORY.md"}


def is_impl_file(path: str) -> bool:
    _, ext = os.path.splitext(path)
    return ext.lower() in IMPL_EXTS


def is_kit_config(path: str) -> bool:
    if os.path.basename(path) in KIT_BASENAMES:
        return True
    rel = path if not os.path.isabs(path) else os.path.relpath(path)
    return rel.startswith(".claude/") or rel.startswith(".claude" + os.sep)


def is_in_worktree(path: str) -> bool:
    abs_path = os.path.abspath(path)
    worktrees_abs = os.path.abspath(".claude/worktrees")
    return abs_path.startswith(worktrees_abs + os.sep)


def main() -> None:
    data = json.load(sys.stdin)
    file_path: str = data.get("tool_input", {}).get("file_path", "")

    if not file_path:
        sys.exit(0)
    if not is_impl_file(file_path):
        sys.exit(0)
    if is_kit_config(file_path):
        sys.exit(0)
    if is_in_worktree(file_path):
        sys.exit(0)

    print(f"BLOCKED: '{os.path.basename(file_path)}' must be edited inside a worktree.", file=sys.stderr)
    print("  Run /worktree to create one, then work inside .claude/worktrees/<name>/", file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
