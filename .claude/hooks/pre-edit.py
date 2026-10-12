#!/usr/bin/env python3
"""PreToolUse[Edit] entry point."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anomaly_guard  # noqa: E402
import audit_log  # noqa: E402
import content_guard  # noqa: E402
import doc_comment_guard  # noqa: E402
import doc_length_guard  # noqa: E402
import dynamic_name_guard  # noqa: E402
import reference_notice  # noqa: E402
import tdd_guard  # noqa: E402
import testing_guard  # noqa: E402
import worktree_guard  # noqa: E402
from env_file_guard import is_blocked_env_file  # noqa: E402
from hook_lib import (  # noqa: E402
    block,
    emit_additional_context,
    read_hook_input,
    run_fail_closed,
)


def _block_unsafe_path(file_path: str) -> None:
    anomaly_guard.check_path_escape(file_path)
    worktree_guard.check(file_path)
    if is_blocked_env_file(file_path):
        block(
            f"'{os.path.basename(file_path)}' must not be written. "
            "Use .env.sample or .env.example instead."
        )


def _block_unsafe_content(
    file_path: str, old_string: str, new_string: str, replace_all: bool
) -> None:
    content_guard.check_japanese(new_string, file_path)
    content_guard.check_emoji(new_string, file_path)
    doc_length_guard.check_edit(file_path, old_string, new_string, replace_all)
    dynamic_name_guard.check(file_path, old_string, new_string)
    testing_guard.check_edit(file_path, old_string, new_string, replace_all)
    doc_comment_guard.check_edit(file_path, old_string, new_string, replace_all)
    tdd_guard.check(old_string, file_path)


def main() -> None:
    """Check one Edit call and exit 0 when no guard blocks it."""
    data = read_hook_input()
    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if not file_path:
        sys.exit(0)
    audit_log.record("PreToolUse", "Edit", tool_input)
    old_string = tool_input.get("old_string", "")
    new_string = tool_input.get("new_string", "")
    replace_all = tool_input.get("replace_all", False)
    _block_unsafe_path(file_path)
    _block_unsafe_content(file_path, old_string, new_string, replace_all)
    notices = reference_notice.for_edit(file_path, old_string, new_string)
    emit_additional_context("PreToolUse", notices)
    sys.exit(0)


if __name__ == "__main__":
    run_fail_closed(main)
