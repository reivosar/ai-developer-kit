"""Tests for coverage_guard: Go, Rust, and TypeScript files are held to the threshold."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import coverage_guard  # noqa: E402
import coverage_runners  # noqa: E402

COMMIT = "git commit -m 'add discount'"
OTHER_LANGUAGES = [
    ("orders.go", "go_percents"),
    ("src/lib.rs", "rust_percents"),
    ("src/order.ts", "typescript_percents"),
]


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


def _fail_to_measure() -> dict:
    raise AssertionError("coverage must not be measured for this file")


@pytest.mark.parametrize("file_name, runner", OTHER_LANGUAGES)
def test_check_staged_coverage_with_file_below_threshold_in_language_exits_2(
    project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture,
    file_name: str, runner: str,
):
    _stage(project, file_name, "source\n")
    monkeypatch.setattr(coverage_runners, runner, lambda: {file_name: 50.0})
    assert f"{file_name}: 50%" in _blocked_reasons(capsys)


@pytest.mark.parametrize("file_name, runner", OTHER_LANGUAGES)
def test_check_staged_coverage_with_file_absent_from_report_reports_zero(
    project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture,
    file_name: str, runner: str,
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
    _stage(project, "orders.py", "def discount(total):\n    return total\n")
    _stage(project, "orders.go", "source\n")
    monkeypatch.setattr(coverage_runners, "go_percents", lambda: {"orders.go": 40.0})
    reasons = _blocked_reasons(capsys)
    assert "orders.py: 0%" in reasons
    assert "orders.go: 40%" in reasons
    assert "pytest --cov=. --cov-branch --cov-report=term-missing" in reasons
    assert "go test ./... -cover" in reasons
