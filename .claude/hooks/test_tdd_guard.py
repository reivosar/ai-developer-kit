"""Tests for tdd_guard: an implementation change needs a test first."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tdd_guard  # noqa: E402

CANCEL = "def cancel_order(order_id):\n    return order_id\n"
CANCEL_TEST = "assert cancel_order(1) == 1\n"


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _stage(project: Path, name: str, content: str) -> None:
    (project / name).write_text(content)
    subprocess.run(["git", "-C", str(project), "add", name], check=True)


@pytest.mark.parametrize(
    "file_name",
    [
        "test_orders.py",
        "orders_test.go",
        "orders.test.ts",
        "orders.spec.ts",
        "OrderTest.java",
        "OrderSpec.kt",
        "src/tests/orders.py",
    ],
)
def test_is_test_file_with_test_file_name_returns_true(file_name: str):
    assert tdd_guard.is_test_file(file_name) is True


@pytest.mark.parametrize(
    "file_name",
    ["latest_orders.py", "contest.py", "attest-orders.js", "orders.py"],
)
def test_is_test_file_with_implementation_file_name_returns_false(
    file_name: str,
):
    assert tdd_guard.is_test_file(file_name) is False


def test_check_with_no_test_staged_exits_2(project: Path):
    with pytest.raises(SystemExit) as blocked:
        tdd_guard.check(CANCEL, "src/orders.py")
    assert blocked.value.code == 2


def test_check_with_no_test_staged_names_file_and_function_in_message(
    project: Path, capsys: pytest.CaptureFixture
):
    with pytest.raises(SystemExit):
        tdd_guard.check(CANCEL, "src/orders.py")
    message = capsys.readouterr().err
    assert "File: src/orders.py" in message
    assert "Functions being modified: cancel_order" in message
    assert "Write a failing test for these functions first" in message


def test_check_with_staged_test_naming_function_does_not_block(project: Path):
    _stage(project, "test_orders.py", CANCEL_TEST)
    assert tdd_guard.check(CANCEL, "src/orders.py") is None


def test_check_with_staged_test_naming_other_function_exits_2(project: Path):
    _stage(project, "test_orders.py", "assert refund_order(1) == 1\n")
    with pytest.raises(SystemExit) as blocked:
        tdd_guard.check(CANCEL, "src/orders.py")
    assert blocked.value.code == 2


def test_check_with_staged_test_deleted_from_disk_exits_2(project: Path):
    _stage(project, "test_orders.py", CANCEL_TEST)
    (project / "test_orders.py").unlink()
    with pytest.raises(SystemExit) as blocked:
        tdd_guard.check(CANCEL, "src/orders.py")
    assert blocked.value.code == 2


def test_check_when_git_cannot_run_exits_2(
    project: Path, monkeypatch: pytest.MonkeyPatch
):
    def fail_to_run(command: list, **options: object) -> None:
        raise OSError("git is not installed")

    monkeypatch.setattr(tdd_guard.subprocess, "run", fail_to_run)
    with pytest.raises(SystemExit) as blocked:
        tdd_guard.check(CANCEL, "src/orders.py")
    assert blocked.value.code == 2


def test_check_with_file_inside_worktree_and_no_test_exits_2(project: Path):
    worktree = project / ".claude" / "worktrees" / "cancel-order"
    with pytest.raises(SystemExit) as blocked:
        tdd_guard.check(CANCEL, str(worktree / "src" / "orders.py"))
    assert blocked.value.code == 2


def test_check_with_hook_module_and_no_test_exits_2(project: Path):
    with pytest.raises(SystemExit) as blocked:
        tdd_guard.check(CANCEL, ".claude/hooks/order_guard.py")
    assert blocked.value.code == 2


@pytest.mark.parametrize(
    "file_path",
    [
        ".claude/settings.json",
        ".claude/docs/coding.md",
        ".claude/hooks/notify.sh",
        "CLAUDE.md",
        "test_orders.py",
        "Makefile",
    ],
)
def test_check_with_file_that_is_not_implementation_does_not_block(
    project: Path, file_path: str
):
    assert tdd_guard.check(CANCEL, file_path) is None


def test_check_with_private_helper_and_staged_module_test_does_not_block(
    project: Path,
):
    _stage(project, "test_orders.py", CANCEL_TEST)
    helper = "def _total(items):\n    return sum(items)\n"
    assert tdd_guard.check(helper, "src/orders.py") is None


def test_check_with_private_helper_and_other_module_test_exits_2(
    project: Path,
):
    _stage(project, "test_refunds.py", CANCEL_TEST)
    helper = "def _total(items):\n    return sum(items)\n"
    with pytest.raises(SystemExit) as blocked:
        tdd_guard.check(helper, "src/orders.py")
    assert blocked.value.code == 2


def test_check_with_staged_test_naming_module_file_does_not_block(
    project: Path,
):
    _stage(project, "test_guard_wiring.py", 'HOOK = "pre-edit.py"\n')
    assert tdd_guard.check("LIMIT = 1\n", "hooks/pre-edit.py") is None


def test_check_with_staged_test_naming_other_module_file_exits_2(
    project: Path,
):
    _stage(project, "test_guard_wiring.py", 'HOOK = "pre-write.py"\n')
    with pytest.raises(SystemExit) as blocked:
        tdd_guard.check("LIMIT = 1\n", "hooks/pre-edit.py")
    assert blocked.value.code == 2


def test_check_with_hyphenated_file_and_underscored_test_does_not_block(
    project: Path,
):
    _stage(project, "test_pre_edit.py", "assert run_hook() == 0\n")
    assert tdd_guard.check("LIMIT = 1\n", "hooks/pre-edit.py") is None


def test_check_with_guard_disabled_does_not_block(
    project: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("TDD_GUARD_DISABLE", "1")
    assert tdd_guard.check(CANCEL, "src/orders.py") is None
