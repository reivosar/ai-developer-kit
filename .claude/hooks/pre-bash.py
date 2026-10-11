#!/usr/bin/env python3
"""PreToolUse[Bash] entry point."""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anomaly_guard  # noqa: E402
import audit_log  # noqa: E402
import commit_guard  # noqa: E402
import coverage_guard  # noqa: E402
import rate_limiter  # noqa: E402
from bash_guard import (  # noqa: E402
    check_python3_path,
    check_raw_operators,
    is_denied,
    is_whitelisted,
    load_patterns,
)
from cp_guard import check_cp_destination, check_cp_options, check_cp_source  # noqa: E402
from git_guard import (  # noqa: E402
    check_branch_force_delete,
    check_checkout_discard,
    check_commit_on_main,
    check_stash_destructive,
)
from hook_lib import block, read_hook_input, run_fail_closed  # noqa: E402


def main() -> None:
    settings_path = str(Path(__file__).resolve().parent.parent / "settings.json")
    data = read_hook_input()
    tool_input = data.get("tool_input", {})
    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)
    session_id = data.get("session_id", "unknown")
    audit_log.record("PreToolUse", "Bash", tool_input)
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
    check_stash_destructive(command)
    check_checkout_discard(command)
    check_branch_force_delete(command)
    check_commit_on_main(command)
    check_cp_destination(command)
    check_cp_options(command)
    check_cp_source(command)
    check_python3_path(command)
    commit_guard.check_pre_commit(command)
    coverage_guard.check_staged_coverage(command)
    anomaly_guard.check_sensitive_path(command)
    rate_limiter.check_rate(session_id, "bash")
    sys.exit(0)


if __name__ == "__main__":
    run_fail_closed(main)
