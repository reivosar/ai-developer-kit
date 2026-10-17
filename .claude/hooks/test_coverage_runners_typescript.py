"""Tests for coverage_runners: TypeScript coverage per file under vitest or jest."""
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import coverage_runners  # noqa: E402

FAKE_NPX = """#!/bin/sh
echo "npx $*" >> "$CALLS"
for argument in "$@"; do
    case "$argument" in
        --coverage.reportsDirectory=*|--coverageDirectory=*)
            printf '%s' "$REPORT" > "${argument#*=}/coverage-summary.json" ;;
    esac
done
exit "${STATUS:-0}"
"""


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    (tmp_path / "bin").mkdir()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PATH", str(tmp_path / "bin"))
    monkeypatch.setenv("CALLS", str(tmp_path / "calls.log"))
    npx = tmp_path / "bin" / "npx"
    npx.write_text(FAKE_NPX)
    npx.chmod(0o755)
    return tmp_path


def _blocked_reasons(capsys: pytest.CaptureFixture) -> str:
    with pytest.raises(SystemExit) as blocked:
        coverage_runners.typescript_percents()
    assert blocked.value.code == 2
    return capsys.readouterr().err


def _typescript_summary(project: Path, lines: object, branches: object) -> str:
    entry = {"lines": {"pct": lines}, "branches": {"pct": branches}}
    source = str(project / "src" / "order.ts")
    return json.dumps({"total": entry, source: entry})


@pytest.mark.parametrize(
    "runner, command",
    [
        ("vitest", "npx --no-install vitest run --coverage"),
        ("jest", "npx --no-install jest --coverage"),
    ],
)
def test_typescript_percents_runs_the_runner_package_json_names(
    project: Path, monkeypatch: pytest.MonkeyPatch, runner: str, command: str
):
    package = {"devDependencies": {runner: "^1.0.0", "typescript": "^5.0.0"}}
    (project / "package.json").write_text(json.dumps(package))
    monkeypatch.setenv("REPORT", _typescript_summary(project, 100, 50))
    assert coverage_runners.typescript_percents() == {"src/order.ts": 50}
    calls = (project / "calls.log").read_text().splitlines()
    assert calls[0].startswith(command)


def test_typescript_percents_with_unknown_percent_counts_it_as_covered(
    project: Path, monkeypatch: pytest.MonkeyPatch
):
    (project / "package.json").write_text('{"dependencies": {"vitest": "1"}}')
    monkeypatch.setenv("REPORT", _typescript_summary(project, 80, "Unknown"))
    assert coverage_runners.typescript_percents() == {"src/order.ts": 80}


@pytest.mark.parametrize("package", ['{"devDependencies": {"mocha": "1"}}', "{"])
def test_typescript_percents_without_supported_runner_exits_2(
    project: Path, capsys: pytest.CaptureFixture, package: str
):
    (project / "package.json").write_text(package)
    assert "package.json names neither vitest nor jest" in _blocked_reasons(capsys)


def test_typescript_percents_when_runner_cannot_start_exits_2(
    project: Path, capsys: pytest.CaptureFixture
):
    (project / "bin" / "npx").unlink()
    (project / "package.json").write_text('{"devDependencies": {"jest": "1"}}')
    assert "Coverage could not be measured." in _blocked_reasons(capsys)
