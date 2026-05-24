#!/usr/bin/env python3
"""
Pre-tool-call hook for the Write tool.
Blocks Write when the target file already exists — use Edit instead.
Blocks Write to .env* files except .env.sample and .env.example.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env_file_guard import is_blocked_env_file  # noqa: E402
from hook_lib import read_stdin_json, block  # noqa: E402


def main() -> None:
    file_path = read_stdin_json().get("tool_input", {}).get("file_path", "")
    if not file_path:
        sys.exit(0)
    if is_blocked_env_file(file_path):
        block(
            f"'{os.path.basename(file_path)}' must not be written. "
            "Use .env.sample or .env.example instead."
        )
    if os.path.exists(file_path):
        block(f"'{file_path}' already exists. Use Edit to modify existing files.")
    sys.exit(0)


if __name__ == "__main__":
    main()
