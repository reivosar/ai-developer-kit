"""Security integration tests for pre-write.py: audit logging for blocked writes."""
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_records  # noqa: E402

HOOK = Path(__file__).parent / "pre-write.py"


def _records(record_name: str) -> list[dict]:
    [record_file] = hook_records.records_dir().glob(f"*/{record_name}")
    return [json.loads(line) for line in record_file.read_text().splitlines()]


def _run(file_path: str, content: str = "") -> subprocess.CompletedProcess:
    tool_input = {"file_path": file_path, "content": content}
    payload = json.dumps({"tool_name": "Write", "tool_input": tool_input})
    env = {**os.environ, "WORKTREE_GUARD_DISABLE": "1"}
    return subprocess.run(
        [sys.executable, str(HOOK)], input=payload, capture_output=True, text=True, env=env
    )


def test_pre_write_writes_audit_entry_for_blocked_outside_repo_write():
    result = _run("/tmp/throwaway.py", "print('hi')")
    assert result.returncode == 2, "Sanity check: /tmp/ write should be blocked"
    [entry] = _records("audit.jsonl")
    assert entry["tool_name"] == "Write"
    assert entry["hook_event"] == "PreToolUse"


def test_pre_write_blocking_outside_repo_write_records_the_block():
    result = _run("/tmp/throwaway.py", "print('hi')")
    assert result.returncode == 2, result.stderr
    [entry] = _records("blocks/pre-write.jsonl")
    assert entry["guard"] == "pre-write"
    assert entry["hook"] == "pre-write.py"
    assert entry["details"] == [
        "Do not stage content in /tmp/ or other external paths."
    ]
