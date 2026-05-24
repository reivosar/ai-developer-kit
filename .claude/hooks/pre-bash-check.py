#!/usr/bin/env python3
"""
Allow-list check for Bash commands.
Exit 0 = allowed, Exit 2 = blocked.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hook_lib import read_stdin_json, block  # noqa: E402
from bash_guard import (  # noqa: E402
    check_raw_operators, load_patterns, is_whitelisted, is_denied, check_python3_path,
)
from git_guard import (  # noqa: E402
    check_stash_destructive, check_checkout_discard,
    check_branch_force_delete, check_commit_on_main,
)
from cp_guard import check_cp_destination, check_cp_options  # noqa: E402


def run_blocklist_checks(command: str) -> None:
    check_stash_destructive(command)
    check_checkout_discard(command)
    check_branch_force_delete(command)
    check_commit_on_main(command)
    check_cp_destination(command)
    check_cp_options(command)
    check_python3_path(command)


def main() -> None:
    settings_path = str(Path(__file__).resolve().parent.parent / 'settings.json')
    command = read_stdin_json().get("tool_input", {}).get("command", "")
    if not command:
        sys.exit(0)

    check_raw_operators(command)

    try:
        allow_patterns = load_patterns(settings_path, "allow")
        deny_patterns = load_patterns(settings_path, "deny")
    except Exception as e:
        block(f"could not read settings.json — {e}")

    if not is_whitelisted(command, allow_patterns):
        block(f"command not in allow list: {command[:300]}")

    if is_denied(command, deny_patterns):
        block(f"command matches deny list: {command[:300]}")

    run_blocklist_checks(command)
    sys.exit(0)


if __name__ == "__main__":
    main()
