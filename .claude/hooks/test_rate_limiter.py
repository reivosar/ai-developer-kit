"""Tests for rate_limiter.check_rate."""
import json
import sys
import time
from pathlib import Path

import pytest

HOOKS_DIR = str(Path(__file__).resolve().parent)
sys.path.insert(0, HOOKS_DIR)

import rate_limiter  # noqa: E402


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


def test_check_rate_with_limit_disabled_does_not_count_calls(
    tmp_path, monkeypatch
):
    state_file = tmp_path / "rate-state.json"
    monkeypatch.setenv("RATE_LIMIT_DISABLE", "1")
    for _ in range(31):
        rate_limiter.check_rate("sess1", "bash", state_file=state_file)
    assert not state_file.exists()


def test_check_rate_without_state_file_uses_repository_state(
    tmp_path, monkeypatch
):
    monkeypatch.delenv("RATE_LIMIT_DISABLE", raising=False)
    monkeypatch.delenv("RATE_STATE_FILE")
    monkeypatch.setattr(rate_limiter.hook_lib, "REPO_ROOT", tmp_path)
    rate_limiter.check_rate("sess1", "bash")
    state_text = (tmp_path / ".claude" / "rate-state.json").read_text()
    assert len(json.loads(state_text)["sess1"]["bash"]) == 1


def test_check_rate_with_state_file_variable_counts_in_that_file(
    tmp_path, monkeypatch
):
    monkeypatch.delenv("RATE_LIMIT_DISABLE", raising=False)
    named_file = tmp_path / "elsewhere" / "rate-state.json"
    monkeypatch.setenv("RATE_STATE_FILE", str(named_file))
    rate_limiter.check_rate("sess1", "bash")
    assert len(json.loads(named_file.read_text())["sess1"]["bash"]) == 1


def test_check_rate_state_persists_across_calls(tmp_path):
    state_file = tmp_path / "rate-state.json"
    for _ in range(15):
        rate_limiter.check_rate("sess1", "bash", state_file=state_file)
    for _ in range(15):
        rate_limiter.check_rate("sess1", "bash", state_file=state_file)
    with pytest.raises(SystemExit):
        rate_limiter.check_rate("sess1", "bash", state_file=state_file)
