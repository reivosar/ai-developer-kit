#!/usr/bin/env python3
"""PreToolUse[Write] entry point."""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audit_log  # noqa: E402
import content_guard  # noqa: E402
import doc_length_guard  # noqa: E402
import dynamic_name_guard  # noqa: E402
import reference_notice  # noqa: E402
import tdd_guard  # noqa: E402
import worktree_guard  # noqa: E402
from env_file_guard import is_blocked_env_file  # noqa: E402
from hook_lib import (  # noqa: E402
    REPO_ROOT,
    block,
    emit_additional_context,
    read_stdin_json,
)


def _block_unsafe_path(file_path: str) -> None:
    try:
        Path(file_path).resolve().relative_to(REPO_ROOT)
    except ValueError:
        block(
            f"Write to '{file_path}' is outside the project root"
            " and is not permitted.",
            "Do not stage content in /tmp/ or other external paths.",
        )
    worktree_guard.check(file_path)
    if is_blocked_env_file(file_path):
        block(
            f"'{os.path.basename(file_path)}' must not be written. "
            "Use .env.sample or .env.example instead."
        )
    if os.path.exists(file_path):
        block(
            f"'{file_path}' already exists."
            " Use Edit to modify existing files."
        )


def _block_unsafe_content(file_path: str, content: str) -> None:
    content_guard.check_japanese(content, file_path)
    content_guard.check_emoji(content, file_path)
    doc_length_guard.check_write(file_path, content)
    dynamic_name_guard.check(file_path, "", content)
    tdd_guard.check(content, file_path)


def main() -> None:
    data = read_stdin_json()
    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if not file_path:
        sys.exit(0)
    audit_log.record("PreToolUse", "Write", tool_input)
    content = tool_input.get("content", "")
    _block_unsafe_path(file_path)
    _block_unsafe_content(file_path, content)
    notices = reference_notice.for_write(file_path, content)
    emit_additional_context("PreToolUse", notices)
    sys.exit(0)


if __name__ == "__main__":
    main()
