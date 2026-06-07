#!/usr/bin/env python3
"""PreToolUse[Write] entry point."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_guard  # noqa: E402
import tdd_guard  # noqa: E402
import worktree_guard  # noqa: E402
from env_file_guard import is_blocked_env_file  # noqa: E402
from hook_lib import read_stdin_json, block  # noqa: E402


def main() -> None:
    data = read_stdin_json()
    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if not file_path:
        sys.exit(0)
    worktree_guard.check(file_path)
    if is_blocked_env_file(file_path):
        block(
            f"'{os.path.basename(file_path)}' must not be written. "
            "Use .env.sample or .env.example instead."
        )
    if os.path.exists(file_path):
        block(f"'{file_path}' already exists. Use Edit to modify existing files.")
    content = tool_input.get("content", "")
    content_guard.check_japanese(content, file_path)
    content_guard.check_emoji(content, file_path)
    tdd_guard.check(content, file_path)
    sys.exit(0)


if __name__ == "__main__":
    main()
