"""Security integration tests for pre-bash.py: audit logging and rate limiting."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hook_lib import REPO_ROOT  # noqa: E402

HOOK = Path(__file__).parent / "pre-bash.py"
RATE_STATE = REPO_ROOT / ".claude" / "rate-state.json"
AUDIT_LOG = REPO_ROOT / ".claude" / "audit.log"


def _run(
    command: str,
    session_id: str = "test-bash-session",
    env: Optional[dict] = None,
) -> subprocess.CompletedProcess:
    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "session_id": session_id,
    })
    return subprocess.run(["python3", str(HOOK)], input=payload, capture_output=True, text=True, env=env)


@pytest.fixture()
def seeded_rate_state():
    session_id = "rate-test-bash-session"
    now = time.time()
    original = RATE_STATE.read_text() if RATE_STATE.exists() else None
    state = json.loads(original) if original else {}
    state[session_id] = {"bash": [now - 10] * 30}
    RATE_STATE.parent.mkdir(parents=True, exist_ok=True)
    RATE_STATE.write_text(json.dumps(state))
    yield session_id
    if original is None:
        RATE_STATE.unlink(missing_ok=True)
    else:
        RATE_STATE.write_text(original)


def test_pre_bash_blocks_when_bash_rate_limit_exceeded(seeded_rate_state):
    result = _run("git status", session_id=seeded_rate_state)
    assert result.returncode == 2, (
        f"Expected blocked (exit 2), got {result.returncode}\nstderr: {result.stderr}"
    )


def test_pre_bash_writes_audit_log_entry_before_guards_run():
    line_count_before = len(AUDIT_LOG.read_text().splitlines()) if AUDIT_LOG.exists() else 0
    _run("git status", session_id="audit-test-bash-session")
    assert AUDIT_LOG.exists(), "audit.log was not created"
    lines_after = AUDIT_LOG.read_text().splitlines()
    assert len(lines_after) > line_count_before, "No new audit entry was written to audit.log"
    last_entry = json.loads(lines_after[-1])
    assert last_entry["tool_name"] == "Bash"
    assert last_entry["hook_event"] == "PreToolUse"


def test_pre_bash_does_not_block_when_rate_limit_disabled(seeded_rate_state):
    result = _run(
        "git status",
        session_id=seeded_rate_state,
        env={**os.environ, "RATE_LIMIT_DISABLE": "1"},
    )
    assert result.returncode == 0, (
        f"Expected allowed (exit 0) when rate limit disabled, got {result.returncode}"
    )
