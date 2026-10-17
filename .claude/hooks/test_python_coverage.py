"""Tests for python_coverage: measuring a project's Python tests, tools included."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import coverage_guard  # noqa: E402
import python_coverage  # noqa: E402

COMMIT = "git commit -m 'add discount'"
ORDERS = (
    "def discount(total):\n"
    "    if total > 100:\n"
    "        return total - 10\n"
    "    return total\n"
)
BOTH_BRANCHES_TEST = (
    "from orders import discount\n\n\n"
    "def test_discount_over_limit_reduces_total():\n"
    "    assert discount(200) == 190\n\n\n"
    "def test_discount_under_limit_keeps_total():\n"
    "    assert discount(50) == 50\n"
)


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    subprocess.run(["git", "init", "-q", "-b", "feat/discount", str(tmp_path)], check=True)
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("COVERAGE_GUARD_DISABLE", raising=False)
    return tmp_path


def _stage(project: Path, name: str, content: str) -> None:
    (project / name).write_text(content)
    subprocess.run(["git", "-C", str(project), "add", name], check=True)


def _blocked_reasons(capsys: pytest.CaptureFixture) -> str:
    with pytest.raises(SystemExit) as blocked:
        coverage_guard.check_staged_coverage(COMMIT)
    assert blocked.value.code == 2
    return capsys.readouterr().err


def _pytest_result(returncode: int) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(
        [], returncode, stdout="", stderr="pytest: error: unrecognized"
    )


def test_measure_when_pytest_cannot_run_exits_2(
    project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    def fail_to_run(command: list, **options: object) -> None:
        raise OSError("pytest is not installed")

    _stage(project, "orders.py", ORDERS)
    monkeypatch.setattr(python_coverage, "_run_tests", fail_to_run)
    assert "could not be measured" in _blocked_reasons(capsys)


def test_measure_when_pytest_rejects_arguments_exits_2(
    project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    _stage(project, "orders.py", ORDERS)
    monkeypatch.setattr(python_coverage, "_run_tests", lambda report: _pytest_result(4))
    assert "could not be measured" in _blocked_reasons(capsys)


def test_measure_when_no_test_writes_no_report_reports_zero(
    project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    _stage(project, "orders.py", ORDERS)
    monkeypatch.setattr(python_coverage, "_run_tests", lambda report: _pytest_result(5))
    assert "orders.py: 0%" in _blocked_reasons(capsys)


def _installer(project: Path, status: int) -> Path:
    script = project / "install-tool.sh"
    script.write_text(
        "#!/bin/sh\n"
        f'echo "$@" >> "{project}/installed.log"\n'
        "echo 'ERROR: could not install pytest.' >&2\n"
        f"exit {status}\n"
    )
    script.chmod(0o755)
    return script


def _raise_missing_pytest() -> None:
    raise FileNotFoundError("pytest")


def _missing_plugin_result() -> subprocess.CompletedProcess:
    rejected = "pytest: error: unrecognized arguments: --cov=. --cov-branch"
    return subprocess.CompletedProcess([], 4, stdout="", stderr=rejected)


def _fail_first_test_run(monkeypatch: pytest.MonkeyPatch, failure) -> None:
    run_tests = python_coverage._run_tests
    attempts = []

    def run_after_first_failure(report_path: str):
        attempts.append(report_path)
        return failure() if len(attempts) == 1 else run_tests(report_path)

    monkeypatch.setattr(python_coverage, "_run_tests", run_after_first_failure)


@pytest.mark.parametrize("failure", [_raise_missing_pytest, _missing_plugin_result])
def test_measure_when_test_tool_is_missing_installs_it_and_measures(
    project: Path, monkeypatch: pytest.MonkeyPatch, failure
):
    _stage(project, "orders.py", ORDERS)
    _stage(project, "test_orders.py", BOTH_BRANCHES_TEST)
    _fail_first_test_run(monkeypatch, failure)
    monkeypatch.setattr(python_coverage, "INSTALLER", _installer(project, 0))
    assert coverage_guard.check_staged_coverage(COMMIT) is None
    assert (project / "installed.log").read_text() == "pytest pytest-cov\n"


def test_measure_when_test_tool_cannot_be_installed_exits_2(
    project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    _stage(project, "orders.py", ORDERS)
    _fail_first_test_run(monkeypatch, _raise_missing_pytest)
    monkeypatch.setattr(python_coverage, "INSTALLER", _installer(project, 1))
    reasons = _blocked_reasons(capsys)
    assert "pytest and pytest-cov are not installed" in reasons
    assert "could not install pytest" in reasons


def test_measure_when_pytest_is_missing_after_install_exits_2(
    project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    _stage(project, "orders.py", ORDERS)
    monkeypatch.setattr(
        python_coverage, "_run_tests", lambda report: _raise_missing_pytest()
    )
    monkeypatch.setattr(python_coverage, "INSTALLER", _installer(project, 0))
    assert "could not be measured" in _blocked_reasons(capsys)
    assert (project / "installed.log").read_text() == "pytest pytest-cov\n"
