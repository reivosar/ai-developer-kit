"""Tests for audit_log.record."""
import json
import sys
from pathlib import Path

import pytest

HOOKS_DIR = str(Path(__file__).resolve().parent)
sys.path.insert(0, HOOKS_DIR)

import audit_log


def test_record_writes_single_jsonl_entry(tmp_path):
    log_file = tmp_path / "audit.log"
    audit_log.record("PostToolUse", "Bash", {"command": "git status"}, log_file=log_file)
    lines = log_file.read_text().strip().split("\n")
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["tool_name"] == "Bash"
    assert entry["hook_event"] == "PostToolUse"
    assert entry["tool_input"]["command"] == "git status"
    assert "timestamp" in entry


def test_record_masks_api_key_field(tmp_path):
    log_file = tmp_path / "audit.log"
    audit_log.record(
        "PreToolUse", "mcp__vault__read",
        {"api_key": "super-secret", "path": "/data"},
        log_file=log_file,
    )
    entry = json.loads(log_file.read_text().strip())
    assert entry["tool_input"]["api_key"] == "***"
    assert entry["tool_input"]["path"] == "/data"


def test_record_masks_password_field(tmp_path):
    log_file = tmp_path / "audit.log"
    audit_log.record("PreToolUse", "Bash", {"password": "secret123"}, log_file=log_file)
    entry = json.loads(log_file.read_text().strip())
    assert entry["tool_input"]["password"] == "***"


def test_record_masks_token_field(tmp_path):
    log_file = tmp_path / "audit.log"
    audit_log.record("PreToolUse", "Bash", {"auth_token": "tok_abc"}, log_file=log_file)
    entry = json.loads(log_file.read_text().strip())
    assert entry["tool_input"]["auth_token"] == "***"


def test_record_with_empty_tool_input_does_not_raise(tmp_path):
    log_file = tmp_path / "audit.log"
    audit_log.record("PostToolUse", "Write", {}, log_file=log_file)
    entry = json.loads(log_file.read_text().strip())
    assert entry["tool_input"] == {}


def test_record_appends_multiple_entries(tmp_path):
    log_file = tmp_path / "audit.log"
    audit_log.record("PostToolUse", "Bash", {"command": "ls"}, log_file=log_file)
    audit_log.record("PostToolUse", "Bash", {"command": "pwd"}, log_file=log_file)
    lines = log_file.read_text().strip().split("\n")
    assert len(lines) == 2
    assert json.loads(lines[0])["tool_input"]["command"] == "ls"
    assert json.loads(lines[1])["tool_input"]["command"] == "pwd"


def test_record_with_unwritable_path_does_not_raise():
    log_file = Path("/nonexistent_dir/audit.log")
    audit_log.record("PostToolUse", "Bash", {"command": "ls"}, log_file=log_file)
