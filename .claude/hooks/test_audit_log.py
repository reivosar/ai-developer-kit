"""Tests for audit_log.record."""
import json
import sys
from pathlib import Path

import pytest

HOOKS_DIR = str(Path(__file__).resolve().parent)
sys.path.insert(0, HOOKS_DIR)

import audit_log  # noqa: E402


def _audit_entries() -> list[dict]:
    audit_file = audit_log.hook_lib.session_records_dir() / "audit.jsonl"
    return [json.loads(line) for line in audit_file.read_text().splitlines()]


def test_record_writes_single_jsonl_entry():
    audit_log.record("PostToolUse", "Bash", {"command": "git status"})
    [entry] = _audit_entries()
    assert entry["tool_name"] == "Bash"
    assert entry["hook_event"] == "PostToolUse"
    assert entry["tool_input"]["command"] == "git status"


def test_record_writes_to_the_directory_of_the_session():
    audit_log.hook_lib.remember_session({"session_id": "5a429071-2390"})
    audit_log.record("PostToolUse", "Bash", {"command": "git status"})
    [entry] = _audit_entries()
    session_directory = audit_log.hook_lib.session_records_dir()
    assert entry["timestamp"].endswith("+00:00")
    assert session_directory.name == entry["timestamp"][:10] + "_5a429071"


def test_record_masks_api_key_field():
    audit_log.record(
        "PreToolUse", "mcp__vault__read", {"api_key": "super-secret", "path": "/data"}
    )
    [entry] = _audit_entries()
    assert entry["tool_input"]["api_key"] == "***"
    assert entry["tool_input"]["path"] == "/data"


def test_record_masks_password_field():
    audit_log.record("PreToolUse", "Bash", {"password": "secret123"})
    [entry] = _audit_entries()
    assert entry["tool_input"]["password"] == "***"


def test_record_masks_token_field():
    audit_log.record("PreToolUse", "Bash", {"auth_token": "tok_abc"})
    [entry] = _audit_entries()
    assert entry["tool_input"]["auth_token"] == "***"


def test_record_with_empty_tool_input_does_not_raise():
    audit_log.record("PostToolUse", "Write", {})
    [entry] = _audit_entries()
    assert entry["tool_input"] == {}


def test_record_appends_multiple_entries():
    audit_log.record("PostToolUse", "Bash", {"command": "ls"})
    audit_log.record("PostToolUse", "Bash", {"command": "pwd"})
    commands = [entry["tool_input"]["command"] for entry in _audit_entries()]
    assert commands == ["ls", "pwd"]


def test_record_with_unwritable_records_directory_does_not_raise(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    occupied = tmp_path / "occupied"
    occupied.write_text("a file where the records directory should be")
    monkeypatch.setenv("HOOK_RECORDS_DIR", str(occupied))
    recorded = audit_log.record("PostToolUse", "Bash", {"command": "ls"})
    assert recorded is None
