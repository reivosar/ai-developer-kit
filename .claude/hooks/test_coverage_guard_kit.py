"""Tests for coverage_guard: a commit that stages a kit hook runs the kit's coverage test."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import coverage_guard  # noqa: E402

COMMIT = "git commit -m 'add discount'"
ORDERS = "def discount(total):\n    return total\n"


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    subprocess.run(["git", "init", "-q", "-b", "feat/discount", str(tmp_path)], check=True)
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("COVERAGE_GUARD_DISABLE", raising=False)
    return tmp_path


def _stage(project: Path, name: str, content: str) -> None:
    target = project / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    subprocess.run(["git", "-C", str(project), "add", name], check=True)


def _blocked_reasons(capsys: pytest.CaptureFixture) -> str:
    with pytest.raises(SystemExit) as blocked:
        coverage_guard.check_staged_coverage(COMMIT)
    assert blocked.value.code == 2
    return capsys.readouterr().err


def _must_not_run() -> None:
    raise AssertionError("the kit's coverage test was started")


def _kit_test_result(status: int):
    def run() -> subprocess.CompletedProcess:
        output = "FAILED test_every_hook_module_meets_coverage_threshold"
        return subprocess.CompletedProcess(["pytest"], status, output, "")
    return run


@pytest.mark.parametrize("file_name", ["README.md", ".claude/docs/orders.md"])
def test_check_staged_coverage_without_kit_hook_does_not_run_kit_test(
    project: Path, file_name: str, monkeypatch: pytest.MonkeyPatch
):
    _stage(project, file_name, ORDERS)
    monkeypatch.setattr(coverage_guard, "_run_kit_coverage_test", _must_not_run)
    assert coverage_guard.check_staged_coverage(COMMIT) is None


def test_check_staged_coverage_with_kit_hook_below_threshold_exits_2(
    project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    _stage(project, ".claude/hooks/order_guard.py", ORDERS)
    monkeypatch.setattr(coverage_guard, "_run_kit_coverage_test", _kit_test_result(1))
    reasons = _blocked_reasons(capsys)
    assert "The kit's hooks are below 90% coverage, or a hook test fails." in reasons
    assert "test_every_hook_module_meets_coverage_threshold" in reasons


def test_check_staged_coverage_with_kit_hook_at_threshold_does_not_block(
    project: Path, monkeypatch: pytest.MonkeyPatch
):
    _stage(project, ".claude/hooks/order_guard.py", ORDERS)
    monkeypatch.setattr(coverage_guard, "_run_kit_coverage_test", _kit_test_result(0))
    assert coverage_guard.check_staged_coverage(COMMIT) is None


def test_check_staged_coverage_when_kit_coverage_test_cannot_start_exits_2(
    project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    def fail_to_start() -> None:
        raise FileNotFoundError("pytest")

    _stage(project, ".claude/hooks/order_guard.py", ORDERS)
    monkeypatch.setattr(coverage_guard, "_run_kit_coverage_test", fail_to_start)
    assert "The kit's hook coverage could not be measured." in _blocked_reasons(capsys)


def test_check_staged_coverage_without_kit_coverage_test_does_not_block(
    project: Path, monkeypatch: pytest.MonkeyPatch
):
    _stage(project, ".claude/hooks/order_guard.py", ORDERS)
    monkeypatch.setattr(coverage_guard, "KIT_COVERAGE_TEST", project / "absent.py")
    monkeypatch.setattr(coverage_guard, "_run_kit_coverage_test", _must_not_run)
    assert coverage_guard.check_staged_coverage(COMMIT) is None


def test_run_kit_coverage_test_runs_pytest_on_the_kit_coverage_test(
    monkeypatch: pytest.MonkeyPatch,
):
    calls = []

    def run(command: list, **options: object) -> subprocess.CompletedProcess:
        calls.append((command, options["env"]))
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(coverage_guard.subprocess, "run", run)
    coverage_guard._run_kit_coverage_test()
    [(command, environment)] = calls
    assert command[0] == "pytest"
    assert command[-1] == str(coverage_guard.KIT_COVERAGE_TEST)
    assert environment["COVERAGE_GUARD_DISABLE"] == "1"
