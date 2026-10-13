#!/usr/bin/env python3
"""PreToolUse[Bash] entry point."""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fail_closed  # noqa: E402

# Installed before the guards are imported: one that fails to load must block
# the command, not let it through unchecked.
fail_closed.install()
import anomaly_guard  # noqa: E402
import audit_log  # noqa: E402
import commit_guard  # noqa: E402
import coverage_guard  # noqa: E402
import rate_limiter  # noqa: E402
import static_analysis_guard  # noqa: E402
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


SETTINGS_PATH = str(Path(__file__).resolve().parent.parent / "settings.json")


def _block_unlisted_command(command: str) -> None:
    try:
        allow_patterns = load_patterns(SETTINGS_PATH, "allow")
        deny_patterns = load_patterns(SETTINGS_PATH, "deny")
    except Exception as e:
        block(f"could not read settings.json — {e}")
    if not is_whitelisted(command, allow_patterns):
        block(f"command not in allow list: {command[:300]}")
    if is_denied(command, deny_patterns):
        block(f"command matches deny list: {command[:300]}")


def _block_unsafe_command(command: str) -> None:
    check_stash_destructive(command)
    check_checkout_discard(command)
    check_branch_force_delete(command)
    check_commit_on_main(command)
    check_cp_destination(command)
    check_cp_options(command)
    check_cp_source(command)
    check_python3_path(command)


def _block_unfit_commit(command: str) -> None:
    # The cheap checks run first: the diff, then the linters, then the tests.
    commit_guard.check_pre_commit(command)
    static_analysis_guard.check_staged_files(command)
    coverage_guard.check_staged_coverage(command)


def main() -> None:
    """Check one Bash call and exit 0 when no guard blocks it."""
    data = read_hook_input()
    tool_input = data.get("tool_input", {})
    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)
    audit_log.record("PreToolUse", "Bash", tool_input)
    check_raw_operators(command)
    _block_unlisted_command(command)
    _block_unsafe_command(command)
    _block_unfit_commit(command)
    anomaly_guard.check_sensitive_path(command)
    rate_limiter.check_rate(data.get("session_id", "unknown"), "bash")
    sys.exit(0)


if __name__ == "__main__":
    run_fail_closed(main)
