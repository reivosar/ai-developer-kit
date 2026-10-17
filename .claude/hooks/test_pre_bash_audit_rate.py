"""Security integration tests for pre-bash.py: records and rate limiting."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_records  # noqa: E402

HOOKS_DIR = Path(__file__).parent
HOOK = HOOKS_DIR / "pre-bash.py"
LAUNCHER = HOOKS_DIR / "run-hook.py"


def _run(
    command: str,
    session_id: str = "test-bash-session",
    env: Optional[dict] = None,
    hook_command: Optional[list] = None,
) -> subprocess.CompletedProcess:
    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "session_id": session_id,
    })
    return subprocess.run(
        hook_command or [sys.executable, str(HOOK)],
        input=payload, capture_output=True, text=True, env=env,
    )


def _session_records(session_name: str, record_name: str) -> list[dict]:
    [record_file] = hook_records.records_dir().glob(f"*_{session_name}/{record_name}")
    return [json.loads(line) for line in record_file.read_text().splitlines()]


@pytest.fixture()
def seeded_rate_state() -> str:
    session_id = "rate-test-bash-session"
    state = {session_id: {"bash": [time.time() - 10] * 30}}
    Path(os.environ["RATE_STATE_FILE"]).write_text(json.dumps(state))
    return session_id


def test_pre_bash_blocks_when_bash_rate_limit_exceeded(seeded_rate_state: str):
    result = _run("git status", session_id=seeded_rate_state)
    assert result.returncode == 2, (
        f"Expected blocked (exit 2), got {result.returncode}\nstderr: {result.stderr}"
    )


def test_pre_bash_writes_audit_entry_to_the_session_directory():
    _run("git status", session_id="a0d17e57-bash-session")
    [entry] = _session_records("a0d17e57", "audit.jsonl")
    assert entry["tool_name"] == "Bash"
    assert entry["hook_event"] == "PreToolUse"


def test_pre_bash_blocking_a_command_records_the_block_under_its_guard():
    result = _run("node --version", session_id="b10c4ed0-bash-session")
    assert result.returncode == 2, result.stderr
    [entry] = _session_records("b10c4ed0", "blocks/pre-bash.jsonl")
    assert entry["guard"] == "pre-bash"
    assert entry["hook"] == "pre-bash.py"
    assert entry["reason"] == "command not in allow list: node --version"


def test_pre_bash_started_by_the_launcher_records_the_hook_name():
    launcher_command = [sys.executable, str(LAUNCHER), "pre-bash.py"]
    result = _run(
        "node --version", session_id="c0ffee00-bash-session",
        hook_command=launcher_command,
    )
    assert result.returncode == 2, result.stderr
    [entry] = _session_records("c0ffee00", "blocks/pre-bash.jsonl")
    assert entry["hook"] == "pre-bash.py"


def test_pre_bash_does_not_block_when_rate_limit_disabled(seeded_rate_state: str):
    result = _run(
        "git status",
        session_id=seeded_rate_state,
        env={**os.environ, "RATE_LIMIT_DISABLE": "1"},
    )
    assert result.returncode == 0, (
        f"Expected allowed (exit 0) when rate limit disabled, got {result.returncode}"
    )
