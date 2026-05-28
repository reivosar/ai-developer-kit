#!/usr/bin/env python3
"""PreToolUse[Edit] entry point."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_guard  # noqa: E402
import tdd_guard  # noqa: E402
from env_file_guard import is_blocked_env_file  # noqa: E402
from hook_lib import read_stdin_json, block  # noqa: E402

def main() -> None:
    data = read_stdin_json()
    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if not file_path:
        sys.exit(0)
    if is_blocked_env_file(file_path):
        block(
            f"'{os.path.basename(file_path)}' must not be written. "
            "Use .env.sample or .env.example instead."
        )
    new_string = tool_input.get("new_string", "")
    content_guard.check_japanese(new_string, file_path)
    content_guard.check_emoji(new_string, file_path)
    old_string = tool_input.get("old_string", "")
    tdd_guard.check(old_string, file_path)
    sys.exit(0)


if __name__ == "__main__":
    main()
