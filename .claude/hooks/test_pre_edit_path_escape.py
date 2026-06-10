"""Security integration tests for pre-edit.py: path escape blocking and audit logging."""
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hook_lib import REPO_ROOT  # noqa: E402

HOOK = Path(__file__).parent / "pre-edit.py"
AUDIT_LOG = REPO_ROOT / ".claude" / "audit.log"


def _run(
    file_path: str,
    old_string: str = "",
    extra_env: Optional[dict] = None,
) -> subprocess.CompletedProcess:
    payload = json.dumps({
        "tool_name": "Edit",
        "tool_input": {"file_path": file_path, "old_string": old_string, "new_string": ""},
    })
    env = {**os.environ, "WORKTREE_GUARD_DISABLE": "1", **(extra_env or {})}
    return subprocess.run(
        ["python3", str(HOOK)], input=payload, capture_output=True, text=True, env=env
    )


def test_pre_edit_blocks_file_path_outside_repo_root():
    # old_string="" bypasses tdd_guard so only the path-escape check can block this
    result = _run("/tmp/evil.py", old_string="")
    assert result.returncode == 2, (
        f"Expected blocked (exit 2), got {result.returncode}\nstderr: {result.stderr}"
    )


def test_pre_edit_allows_file_path_inside_repo_root():
    result = _run(str(HOOK), old_string="")
    assert result.returncode == 0, (
        f"Expected allowed (exit 0), got {result.returncode}\nstderr: {result.stderr}"
    )


def test_pre_edit_writes_audit_log_entry_before_guards_run():
    line_count_before = len(AUDIT_LOG.read_text().splitlines()) if AUDIT_LOG.exists() else 0
    _run(str(HOOK), old_string="")
    assert AUDIT_LOG.exists(), "audit.log was not created"
    lines_after = AUDIT_LOG.read_text().splitlines()
    assert len(lines_after) > line_count_before, "No new audit entry was written to audit.log"
    last_entry = json.loads(lines_after[-1])
    assert last_entry["tool_name"] == "Edit"
    assert last_entry["hook_event"] == "PreToolUse"


def test_pre_edit_allows_outside_repo_when_path_escape_disabled():
    result = _run("/tmp/evil.py", extra_env={"ANOMALY_PATH_ESCAPE_DISABLE": "1"})
    assert result.returncode == 0, (
        f"Expected allowed (exit 0) when path escape disabled, got {result.returncode}"
    )
