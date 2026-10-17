"""Tests for reference_notice through pre-edit.py and pre-write.py."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).parent
OLD_SIGNATURE = "def cancel_order(order_id):"
NEW_SIGNATURE = "def cancel_order(order_id, reason):"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    (root / "orders.py").write_text(OLD_SIGNATURE + "\n    return order_id\n")
    (root / "api.py").write_text("from orders import cancel_order\n\ncancel_order(1)\n")
    (root / "jobs.py").write_text("cancel_order(2)\n")
    return root


def _run_hook(hook_name: str, tool_input: dict) -> subprocess.CompletedProcess:
    env = {
        **os.environ,
        "WORKTREE_GUARD_DISABLE": "1",
        "ANOMALY_PATH_ESCAPE_DISABLE": "1",
        "TDD_GUARD_DISABLE": "1",
    }
    return subprocess.run(
        [sys.executable, str(HOOKS_DIR / hook_name)],
        input=json.dumps({"tool_input": tool_input}),
        capture_output=True, text=True, env=env,
    )


def test_pre_edit_with_changed_signature_returns_context_and_exits_0(
    repo: Path,
):
    tool_input = {
        "file_path": str(repo / "orders.py"),
        "old_string": OLD_SIGNATURE,
        "new_string": NEW_SIGNATURE,
    }
    result = _run_hook("pre-edit.py", tool_input)
    assert result.returncode == 0, result.stderr
    context = json.loads(result.stdout)["hookSpecificOutput"]
    assert context["hookEventName"] == "PreToolUse"
    assert "3 lines in 2 other files" in context["additionalContext"]


def test_pre_edit_with_unchanged_signature_prints_nothing(repo: Path):
    tool_input = {
        "file_path": str(repo / "orders.py"),
        "old_string": "    return order_id",
        "new_string": "    return str(order_id)",
    }
    result = _run_hook("pre-edit.py", tool_input)
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


def test_pre_write_with_existing_definition_returns_context_and_exits_0():
    probe = HOOKS_DIR / "_reference_notice_probe.py"
    content = (
        "def read_stdin_json():\n"
        '    """Return an empty object."""\n'
        "    return {}\n"
    )
    result = _run_hook(
        "pre-write.py", {"file_path": str(probe), "content": content}
    )
    assert result.returncode == 0, result.stderr
    context = json.loads(result.stdout)["hookSpecificOutput"]
    assert "`read_stdin_json` is already defined in" in (
        context["additionalContext"]
    )
    assert ".claude/hooks/hook_lib.py" in context["additionalContext"]
