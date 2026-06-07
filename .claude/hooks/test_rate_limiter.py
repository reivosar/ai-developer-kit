"""Tests for rate_limiter.check_rate."""
import json
import sys
import time
from pathlib import Path

import pytest

HOOKS_DIR = str(Path(__file__).resolve().parent)
sys.path.insert(0, HOOKS_DIR)

import rate_limiter


def test_check_rate_under_bash_limit_passes(tmp_path):
    state_file = tmp_path / "rate-state.json"
    for _ in range(29):
        rate_limiter.check_rate("sess1", "bash", state_file=state_file)


def test_check_rate_at_bash_limit_blocks(tmp_path):
    state_file = tmp_path / "rate-state.json"
    for _ in range(30):
        rate_limiter.check_rate("sess1", "bash", state_file=state_file)
    with pytest.raises(SystemExit) as exc_info:
        rate_limiter.check_rate("sess1", "bash", state_file=state_file)
    assert exc_info.value.code == 2


def test_check_rate_at_mcp_limit_blocks(tmp_path):
    state_file = tmp_path / "rate-state.json"
    for _ in range(10):
        rate_limiter.check_rate("sess1", "mcp", state_file=state_file)
    with pytest.raises(SystemExit) as exc_info:
        rate_limiter.check_rate("sess1", "mcp", state_file=state_file)
    assert exc_info.value.code == 2


def test_check_rate_different_sessions_are_isolated(tmp_path):
    state_file = tmp_path / "rate-state.json"
    for _ in range(30):
        rate_limiter.check_rate("sess1", "bash", state_file=state_file)
    rate_limiter.check_rate("sess2", "bash", state_file=state_file)


def test_check_rate_bash_limit_does_not_affect_mcp(tmp_path):
    state_file = tmp_path / "rate-state.json"
    for _ in range(30):
        rate_limiter.check_rate("sess1", "bash", state_file=state_file)
    rate_limiter.check_rate("sess1", "mcp", state_file=state_file)


def test_check_rate_pruning_removes_old_entries(tmp_path):
    state_file = tmp_path / "rate-state.json"
    old_timestamps = [time.time() - 120] * 30
    state_file.write_text(json.dumps({"sess1": {"bash": old_timestamps}}))
    rate_limiter.check_rate("sess1", "bash", state_file=state_file)


def test_check_rate_state_persists_across_calls(tmp_path):
    state_file = tmp_path / "rate-state.json"
    for _ in range(15):
        rate_limiter.check_rate("sess1", "bash", state_file=state_file)
    for _ in range(15):
        rate_limiter.check_rate("sess1", "bash", state_file=state_file)
    with pytest.raises(SystemExit):
        rate_limiter.check_rate("sess1", "bash", state_file=state_file)
