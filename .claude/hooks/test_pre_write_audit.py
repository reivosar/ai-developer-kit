"""Security integration tests for pre-write.py: audit logging for blocked writes."""
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hook_lib import REPO_ROOT  # noqa: E402

HOOK = Path(__file__).parent / "pre-write.py"
AUDIT_LOG = REPO_ROOT / ".claude" / "audit.log"


def _run(file_path: str, content: str = "") -> subprocess.CompletedProcess:
    payload = json.dumps({"tool_name": "Write", "tool_input": {"file_path": file_path, "content": content}})
    env = {**os.environ, "WORKTREE_GUARD_DISABLE": "1"}
    return subprocess.run(
        ["python3", str(HOOK)], input=payload, capture_output=True, text=True, env=env
    )


def test_pre_write_writes_audit_log_entry_for_blocked_outside_repo_write():
    line_count_before = len(AUDIT_LOG.read_text().splitlines()) if AUDIT_LOG.exists() else 0
    result = _run("/tmp/throwaway.py", "print('hi')")
    assert result.returncode == 2, "Sanity check: /tmp/ write should be blocked"
    assert AUDIT_LOG.exists(), "audit.log was not created"
    lines_after = AUDIT_LOG.read_text().splitlines()
    assert len(lines_after) > line_count_before, "No new audit entry was written to audit.log"
    last_entry = json.loads(lines_after[-1])
    assert last_entry["tool_name"] == "Write"
    assert last_entry["hook_event"] == "PreToolUse"
