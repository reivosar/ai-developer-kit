"""Security integration tests for pre-edit.py: path escape blocking and audit logging."""
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_lib  # noqa: E402

HOOK = Path(__file__).parent / "pre-edit.py"


def _records(record_name: str) -> list[dict]:
    [record_file] = hook_lib.records_dir().glob(f"*/{record_name}")
    return [json.loads(line) for line in record_file.read_text().splitlines()]


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


def test_pre_edit_writes_audit_entry_before_guards_run():
    _run(str(HOOK), old_string="")
    [entry] = _records("audit.jsonl")
    assert entry["tool_name"] == "Edit"
    assert entry["hook_event"] == "PreToolUse"


def test_pre_edit_blocking_a_path_records_the_block_under_its_guard():
    result = _run("/tmp/evil.py", old_string="")
    assert result.returncode == 2, result.stderr
    [entry] = _records("blocks/anomaly_guard.jsonl")
    assert entry["guard"] == "anomaly_guard"
    assert entry["hook"] == "pre-edit.py"


def test_pre_edit_allows_outside_repo_when_path_escape_disabled():
    result = _run("/tmp/evil.py", extra_env={"ANOMALY_PATH_ESCAPE_DISABLE": "1"})
    assert result.returncode == 0, (
        f"Expected allowed (exit 0) when path escape disabled, got {result.returncode}"
    )
