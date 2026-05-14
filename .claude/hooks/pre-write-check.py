#!/usr/bin/env python3
"""
Pre-tool-call hook for the Write tool.
Blocks Write when the target file already exists — use Edit instead.
Blocks Write to .env* files except .env.sample and .env.example.
"""
import sys
import json
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env_file_guard import ALLOWED_ENV_FILES, is_blocked_env_file  # noqa: E402


def read_file_path():
    try:
        data = json.load(sys.stdin)
        return data.get("tool_input", {}).get("file_path", "")
    except Exception:
        return None


def check_file_exists(file_path):
    if os.path.exists(file_path):
        print(
            f"BLOCKED: '{file_path}' already exists. Use Edit to modify existing files.",
            file=sys.stderr,
        )
        sys.exit(2)


def main():
    file_path = read_file_path()
    if not file_path:
        sys.exit(0)
    if is_blocked_env_file(file_path):
        print(
            f"BLOCKED: '{os.path.basename(file_path)}' must not be written. Use .env.sample or .env.example instead.",
            file=sys.stderr,
        )
        sys.exit(2)
    check_file_exists(file_path)
    sys.exit(0)


if __name__ == "__main__":
    main()
