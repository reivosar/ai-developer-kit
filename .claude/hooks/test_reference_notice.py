"""Tests for reference_notice: report references and duplicate definitions."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_lib  # noqa: E402
import reference_notice  # noqa: E402

HOOKS_DIR = Path(__file__).parent
OLD_SIGNATURE = "def cancel_order(order_id):"
NEW_SIGNATURE = "def cancel_order(order_id, reason):"
ORDERS = OLD_SIGNATURE + "\n    return order_id\n"
API = "from orders import cancel_order\n\ncancel_order(1)\n"
JOBS = "cancel_order(2)\n"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    (root / "orders.py").write_text(ORDERS)
    (root / "api.py").write_text(API)
    (root / "jobs.py").write_text(JOBS)
    return root


def _run_hook(hook_name: str, tool_input: dict) -> subprocess.CompletedProcess:
    env = {
        **os.environ,
        "WORKTREE_GUARD_DISABLE": "1",
        "ANOMALY_PATH_ESCAPE_DISABLE": "1",
        "TDD_GUARD_DISABLE": "1",
    }
    return subprocess.run(
        ["python3", str(HOOKS_DIR / hook_name)],
        input=json.dumps({"tool_input": tool_input}),
        capture_output=True,
        text=True,
        env=env,
    )


def test_for_edit_with_changed_signature_reports_reference_count(repo: Path):
    orders = str(repo / "orders.py")
    notices = reference_notice.for_edit(orders, OLD_SIGNATURE, NEW_SIGNATURE)
    assert len(notices) == 1
    assert "`cancel_order` is referenced on 3 lines in 2 other files" in (
        notices[0]
    )
    assert "api.py:1" in notices[0]
    assert "jobs.py:1" in notices[0]


def test_for_edit_with_removed_definition_reports_reference_count(repo: Path):
    orders = str(repo / "orders.py")
    notices = reference_notice.for_edit(orders, ORDERS, "")
    assert len(notices) == 1
    assert "3 lines in 2 other files" in notices[0]


def test_for_edit_with_unchanged_signature_returns_no_notice(repo: Path):
    orders = str(repo / "orders.py")
    edited = OLD_SIGNATURE + "\n    return str(order_id)\n"
    assert reference_notice.for_edit(orders, ORDERS, edited) == []


def test_for_edit_with_unreferenced_function_returns_no_notice(repo: Path):
    jobs = str(repo / "jobs.py")
    old = "def purge_drafts(limit):"
    new = "def purge_drafts(limit, older_than):"
    assert reference_notice.for_edit(jobs, old, new) == []


def test_for_edit_adding_existing_definition_reports_location(repo: Path):
    jobs = str(repo / "jobs.py")
    added = JOBS + "\n\n" + ORDERS
    notices = reference_notice.for_edit(jobs, JOBS, added)
    assert len(notices) == 1
    assert "`cancel_order` is already defined in orders.py:1" in notices[0]


def test_for_write_with_existing_definition_reports_location(repo: Path):
    refunds = str(repo / "refunds.py")
    notices = reference_notice.for_write(refunds, ORDERS)
    assert len(notices) == 1
    assert "`cancel_order` is already defined in orders.py:1" in notices[0]


def test_for_write_in_new_directory_reports_location(repo: Path):
    refunds = str(repo / "refunds" / "handlers" / "refund.py")
    notices = reference_notice.for_write(refunds, ORDERS)
    assert len(notices) == 1
    assert "`cancel_order` is already defined in orders.py:1" in notices[0]


def test_for_write_with_unique_definition_returns_no_notice(repo: Path):
    refunds = str(repo / "refunds.py")
    content = "def refund_order(order_id):\n    return order_id\n"
    assert reference_notice.for_write(refunds, content) == []


@pytest.mark.parametrize("name", ["main", "_cancel_order"])
def test_for_write_with_conventional_or_private_name_returns_no_notice(
    repo: Path, name: str
):
    (repo / "worker.py").write_text(f"def {name}():\n    pass\n")
    cli = str(repo / "cli.py")
    content = f"def {name}():\n    return 0\n"
    assert reference_notice.for_write(cli, content) == []


def test_for_edit_in_test_file_returns_no_notice(repo: Path):
    fixture_holder = str(repo / "test_orders.py")
    notices = reference_notice.for_edit(
        fixture_holder, OLD_SIGNATURE, NEW_SIGNATURE
    )
    assert notices == []


def test_for_edit_outside_git_repository_returns_no_notice(tmp_path: Path):
    orders = tmp_path / "orders.py"
    orders.write_text(ORDERS)
    notices = reference_notice.for_edit(
        str(orders), OLD_SIGNATURE, NEW_SIGNATURE
    )
    assert notices == []


def test_for_edit_when_git_times_out_returns_no_notice(
    repo: Path, monkeypatch: pytest.MonkeyPatch
):
    def time_out(command: list, **options: object) -> None:
        raise subprocess.TimeoutExpired(command, options["timeout"])

    monkeypatch.setattr(reference_notice.subprocess, "run", time_out)
    orders = str(repo / "orders.py")
    notices = reference_notice.for_edit(orders, OLD_SIGNATURE, NEW_SIGNATURE)
    assert notices == []


def test_for_edit_with_notice_disabled_returns_no_notice(
    repo: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("REFERENCE_NOTICE_DISABLE", "1")
    orders = str(repo / "orders.py")
    notices = reference_notice.for_edit(orders, OLD_SIGNATURE, NEW_SIGNATURE)
    assert notices == []


def test_emit_additional_context_with_notices_prints_hook_json(
    capsys: pytest.CaptureFixture,
):
    hook_lib.emit_additional_context("PreToolUse", ["first", "second"])
    output = json.loads(capsys.readouterr().out)
    assert output == {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": "first\nsecond",
        }
    }


def test_emit_additional_context_with_no_notice_prints_nothing(
    capsys: pytest.CaptureFixture,
):
    hook_lib.emit_additional_context("PreToolUse", [])
    assert capsys.readouterr().out == ""


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
    content = "def read_stdin_json():\n    return {}\n"
    result = _run_hook(
        "pre-write.py", {"file_path": str(probe), "content": content}
    )
    assert result.returncode == 0, result.stderr
    context = json.loads(result.stdout)["hookSpecificOutput"]
    assert "`read_stdin_json` is already defined in" in (
        context["additionalContext"]
    )
    assert ".claude/hooks/hook_lib.py" in context["additionalContext"]
