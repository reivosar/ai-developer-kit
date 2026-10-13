"""Tests for coverage_guard: staged code must be covered by its tests."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import coverage_guard  # noqa: E402
import coverage_runners  # noqa: E402

HOOKS_DIR = Path(__file__).parent
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
ONE_BRANCH_TEST = (
    "from orders import discount\n\n\n"
    "def test_discount_under_limit_keeps_total():\n"
    "    assert discount(50) == 50\n"
)
FAILING_TEST = (
    "from orders import discount\n\n\n"
    "def test_discount_under_limit_keeps_total():\n"
    "    assert discount(50) == 0\n"
)


def _summary(covered_branches: int, branches: int, lines: int = 10) -> dict:
    return {
        "summary": {
            "num_branches": branches,
            "covered_branches": covered_branches,
            "num_statements": 10,
            "covered_lines": lines,
        }
    }


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    subprocess.run(
        ["git", "init", "-q", "-b", "feat/discount", str(tmp_path)], check=True
    )
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


def test_uncovered_files_with_all_branches_covered_returns_nothing():
    report = {"files": {"orders.py": _summary(4, 4)}}
    assert coverage_guard.uncovered_files(report, ["orders.py"]) == {}


def test_uncovered_files_at_threshold_returns_nothing():
    report = {"files": {"orders.py": _summary(9, 10, lines=9)}}
    assert coverage_guard.uncovered_files(report, ["orders.py"]) == {}


def test_uncovered_files_with_half_the_branches_reports_percent():
    report = {"files": {"orders.py": _summary(2, 4)}}
    assert coverage_guard.uncovered_files(report, ["orders.py"]) == {
        "orders.py": 50.0
    }


def test_uncovered_files_with_uncovered_lines_and_no_branch_reports_percent():
    report = {"files": {"orders.py": _summary(0, 0, lines=8)}}
    assert coverage_guard.uncovered_files(report, ["orders.py"]) == {
        "orders.py": 80.0
    }


def test_uncovered_files_with_covered_branches_but_missed_lines_reports_lines():
    report = {"files": {"orders.py": _summary(4, 4, lines=5)}}
    assert coverage_guard.uncovered_files(report, ["orders.py"]) == {
        "orders.py": 50.0
    }


def test_uncovered_files_with_file_no_test_imported_reports_zero():
    assert coverage_guard.uncovered_files({"files": {}}, ["orders.py"]) == {
        "orders.py": 0.0
    }


def test_check_staged_coverage_with_covered_file_does_not_block(project: Path):
    _stage(project, "orders.py", ORDERS)
    _stage(project, "test_orders.py", BOTH_BRANCHES_TEST)
    assert coverage_guard.check_staged_coverage(COMMIT) is None


def test_check_staged_coverage_with_untested_branch_exits_2(
    project: Path, capsys: pytest.CaptureFixture
):
    _stage(project, "orders.py", ORDERS)
    _stage(project, "test_orders.py", ONE_BRANCH_TEST)
    reasons = _blocked_reasons(capsys)
    assert "orders.py: 50%" in reasons


def test_check_staged_coverage_with_no_test_at_all_exits_2(
    project: Path, capsys: pytest.CaptureFixture
):
    _stage(project, "orders.py", ORDERS)
    assert "orders.py: 0%" in _blocked_reasons(capsys)


def test_check_staged_coverage_with_failing_test_exits_2(
    project: Path, capsys: pytest.CaptureFixture
):
    _stage(project, "orders.py", ORDERS)
    _stage(project, "test_orders.py", FAILING_TEST)
    assert "tests failed" in _blocked_reasons(capsys)


def test_check_staged_coverage_leaves_no_coverage_file_in_project(project: Path):
    _stage(project, "orders.py", ORDERS)
    _stage(project, "test_orders.py", BOTH_BRANCHES_TEST)
    coverage_guard.check_staged_coverage(COMMIT)
    assert not (project / ".coverage").exists()


@pytest.mark.parametrize(
    "file_name",
    ["README.md", "test_orders.py", ".claude/hooks/order_guard.py"],
)
def test_check_staged_coverage_with_file_that_is_not_measured_does_not_block(
    project: Path, file_name: str
):
    _stage(project, file_name, ORDERS)
    assert coverage_guard.check_staged_coverage(COMMIT) is None


def test_check_staged_coverage_with_other_command_does_not_block(project: Path):
    _stage(project, "orders.py", ORDERS)
    assert coverage_guard.check_staged_coverage("git status") is None


def test_check_staged_coverage_with_guard_disabled_does_not_block(
    project: Path, monkeypatch: pytest.MonkeyPatch
):
    _stage(project, "orders.py", ORDERS)
    monkeypatch.setenv("COVERAGE_GUARD_DISABLE", "1")
    assert coverage_guard.check_staged_coverage(COMMIT) is None


def test_check_staged_coverage_when_pytest_cannot_run_exits_2(
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
):
    def fail_to_run(command: list, **options: object) -> None:
        raise OSError("pytest is not installed")

    _stage(project, "orders.py", ORDERS)
    monkeypatch.setattr(coverage_guard, "_run_tests", fail_to_run)
    assert "could not be measured" in _blocked_reasons(capsys)


def _pytest_result(returncode: int) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(
        [], returncode, stdout="", stderr="pytest: error: unrecognized"
    )


def test_check_staged_coverage_when_pytest_rejects_arguments_exits_2(
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
):
    _stage(project, "orders.py", ORDERS)
    monkeypatch.setattr(
        coverage_guard, "_run_tests", lambda report_path: _pytest_result(4)
    )
    assert "could not be measured" in _blocked_reasons(capsys)


def test_check_staged_coverage_when_no_test_writes_no_report_reports_zero(
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
):
    _stage(project, "orders.py", ORDERS)
    monkeypatch.setattr(
        coverage_guard, "_run_tests", lambda report_path: _pytest_result(5)
    )
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
    run_tests = coverage_guard._run_tests
    attempts = []

    def run_after_first_failure(report_path: str):
        attempts.append(report_path)
        return failure() if len(attempts) == 1 else run_tests(report_path)

    monkeypatch.setattr(coverage_guard, "_run_tests", run_after_first_failure)


@pytest.mark.parametrize("failure", [_raise_missing_pytest, _missing_plugin_result])
def test_check_staged_coverage_when_test_tool_is_missing_installs_it_and_measures(
    project: Path, monkeypatch: pytest.MonkeyPatch, failure
):
    _stage(project, "orders.py", ORDERS)
    _stage(project, "test_orders.py", BOTH_BRANCHES_TEST)
    _fail_first_test_run(monkeypatch, failure)
    monkeypatch.setattr(coverage_guard, "INSTALLER", _installer(project, 0))
    assert coverage_guard.check_staged_coverage(COMMIT) is None
    assert (project / "installed.log").read_text() == "pytest pytest-cov\n"


def test_check_staged_coverage_when_test_tool_cannot_be_installed_exits_2(
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
):
    _stage(project, "orders.py", ORDERS)
    _fail_first_test_run(monkeypatch, _raise_missing_pytest)
    monkeypatch.setattr(coverage_guard, "INSTALLER", _installer(project, 1))
    reasons = _blocked_reasons(capsys)
    assert "pytest and pytest-cov are not installed" in reasons
    assert "could not install pytest" in reasons


def test_check_staged_coverage_when_pytest_is_missing_after_install_exits_2(
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
):
    _stage(project, "orders.py", ORDERS)
    monkeypatch.setattr(
        coverage_guard, "_run_tests", lambda report_path: _raise_missing_pytest()
    )
    monkeypatch.setattr(coverage_guard, "INSTALLER", _installer(project, 0))
    assert "could not be measured" in _blocked_reasons(capsys)
    assert (project / "installed.log").read_text() == "pytest pytest-cov\n"


OTHER_LANGUAGES = [
    ("orders.go", "go_percents"),
    ("src/lib.rs", "rust_percents"),
    ("src/order.ts", "typescript_percents"),
]


def _fail_to_measure() -> dict:
    raise AssertionError("coverage must not be measured for this file")


@pytest.mark.parametrize("file_name, runner", OTHER_LANGUAGES)
def test_check_staged_coverage_with_file_below_threshold_in_language_exits_2(
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
    file_name: str,
    runner: str,
):
    _stage(project, file_name, "source\n")
    monkeypatch.setattr(coverage_runners, runner, lambda: {file_name: 50.0})
    assert f"{file_name}: 50%" in _blocked_reasons(capsys)


@pytest.mark.parametrize("file_name, runner", OTHER_LANGUAGES)
def test_check_staged_coverage_with_file_absent_from_report_reports_zero(
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
    file_name: str,
    runner: str,
):
    _stage(project, file_name, "source\n")
    monkeypatch.setattr(coverage_runners, runner, lambda: {})
    assert f"{file_name}: 0%" in _blocked_reasons(capsys)


@pytest.mark.parametrize("file_name, runner", OTHER_LANGUAGES)
def test_check_staged_coverage_with_covered_file_in_language_does_not_block(
    project: Path, monkeypatch: pytest.MonkeyPatch, file_name: str, runner: str
):
    _stage(project, file_name, "source\n")
    monkeypatch.setattr(coverage_runners, runner, lambda: {file_name: 90.0})
    assert coverage_guard.check_staged_coverage(COMMIT) is None


@pytest.mark.parametrize(
    "file_name",
    ["src/types.d.ts", "vite.config.ts", "src/order.test.ts", "orders_test.go"],
)
def test_check_staged_coverage_with_file_that_holds_no_logic_is_not_measured(
    project: Path, monkeypatch: pytest.MonkeyPatch, file_name: str
):
    _stage(project, file_name, "source\n")
    monkeypatch.setattr(coverage_runners, "go_percents", _fail_to_measure)
    monkeypatch.setattr(coverage_runners, "typescript_percents", _fail_to_measure)
    assert coverage_guard.check_staged_coverage(COMMIT) is None


def test_check_staged_coverage_with_two_languages_reports_both(
    project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    _stage(project, "orders.py", ORDERS)
    _stage(project, "orders.go", "source\n")
    monkeypatch.setattr(coverage_runners, "go_percents", lambda: {"orders.go": 40.0})
    reasons = _blocked_reasons(capsys)
    assert "orders.py: 0%" in reasons
    assert "orders.go: 40%" in reasons
    assert "pytest --cov=. --cov-branch --cov-report=term-missing" in reasons
    assert "go test ./... -cover" in reasons


def test_pre_bash_with_commit_of_untested_branch_exits_2(project: Path):
    _stage(project, "orders.py", ORDERS)
    _stage(project, "test_orders.py", ONE_BRANCH_TEST)
    payload = json.dumps({"tool_input": {"command": COMMIT}})
    env = {**os.environ, "RATE_LIMIT_DISABLE": "1"}
    result = subprocess.run(
        ["python3", str(HOOKS_DIR / "pre-bash.py")],
        input=payload, capture_output=True, text=True, env=env,
    )
    assert result.returncode == 2, result.stderr
    assert "orders.py: 50%" in result.stderr
