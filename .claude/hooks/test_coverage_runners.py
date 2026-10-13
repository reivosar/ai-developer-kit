"""Tests for coverage_runners: coverage per file for Go, Rust, and TypeScript."""
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import coverage_runners  # noqa: E402

GO_PROFILE = (
    "mode: set\n"
    "example.com/orders/orders.go:3.18,5.2 2 1\n"
    "example.com/orders/pkg/fee.go:3.16,5.2 1 0\n"
    "example.com/orders/pkg/fee.go:7.16,9.2 1 0\n"
    "example.com/orders/pkg/fee.go:7.16,9.2 1 3\n"
)
FAKE_GO = """#!/bin/sh
echo "go $*" >> "$CALLS"
if [ "$1" = list ]; then echo example.com/orders; exit 0; fi
for argument in "$@"; do
    case "$argument" in
        -coverprofile=*) printf '%s' "$REPORT" > "${argument#-coverprofile=}" ;;
    esac
done
echo "--- FAIL: TestTotal"
exit "${STATUS:-0}"
"""
FAKE_CARGO = """#!/bin/sh
echo "cargo $*" >> "$CALLS"
for argument in "$@"; do
    case "$argument" in
        --output-path=*) printf '%s' "$REPORT" > "${argument#--output-path=}" ;;
    esac
done
exit "${STATUS:-0}"
"""
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
    return tmp_path


def _fake_tool(project: Path, name: str, script: str) -> Path:
    tool = project / "bin" / name
    tool.write_text(script)
    tool.chmod(0o755)
    return tool


def _calls(project: Path) -> list[str]:
    return (project / "calls.log").read_text().splitlines()


def _blocked_reasons(capsys: pytest.CaptureFixture, measure) -> str:
    with pytest.raises(SystemExit) as blocked:
        measure()
    assert blocked.value.code == 2
    return capsys.readouterr().err


def _rust_report(project: Path, lines: float, regions: float) -> str:
    summary = {
        "lines": {"count": 10, "percent": lines},
        "regions": {"count": 4, "percent": regions},
        "branches": {"count": 0, "percent": 0},
    }
    source = str(project / "src" / "lib.rs")
    files = [{"filename": source, "summary": summary}]
    return json.dumps({"data": [{"files": files}]})


def _typescript_summary(project: Path, lines: object, branches: object) -> str:
    entry = {"lines": {"pct": lines}, "branches": {"pct": branches}}
    source = str(project / "src" / "order.ts")
    return json.dumps({"total": entry, source: entry})


def test_go_profile_percents_counts_statements_per_file():
    percents = coverage_runners.go_profile_percents(GO_PROFILE, "example.com/orders")
    assert percents == {"orders.go": 100.0, "pkg/fee.go": 50.0}


def test_go_percents_runs_the_tests_with_a_cover_profile(
    project: Path, monkeypatch: pytest.MonkeyPatch
):
    _fake_tool(project, "go", FAKE_GO)
    monkeypatch.setenv("REPORT", GO_PROFILE)
    assert coverage_runners.go_percents() == {"orders.go": 100.0, "pkg/fee.go": 50.0}
    assert _calls(project)[0] == "go list -m"
    assert _calls(project)[1].startswith("go test ./... -coverprofile=")


def test_go_percents_when_tests_fail_exits_2(
    project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    _fake_tool(project, "go", FAKE_GO)
    monkeypatch.setenv("STATUS", "1")
    reasons = _blocked_reasons(capsys, coverage_runners.go_percents)
    assert "Coverage was not measured because tests failed." in reasons
    assert "--- FAIL: TestTotal" in reasons


def test_go_percents_when_no_profile_is_written_returns_nothing(project: Path):
    _fake_tool(project, "go", "#!/bin/sh\necho example.com/orders\n")
    assert coverage_runners.go_percents() == {}


def test_rust_percents_takes_the_lower_of_lines_and_regions(
    project: Path, monkeypatch: pytest.MonkeyPatch
):
    _fake_tool(project, "cargo", FAKE_CARGO)
    _fake_tool(project, "cargo-llvm-cov", "#!/bin/sh\n")
    monkeypatch.setenv("REPORT", _rust_report(project, lines=100.0, regions=75.0))
    assert coverage_runners.rust_percents() == {"src/lib.rs": 75.0}
    assert _calls(project)[0].startswith(
        "cargo llvm-cov --json --summary-only --output-path="
    )


def test_rust_percents_when_tests_fail_exits_2(
    project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    _fake_tool(project, "cargo", FAKE_CARGO)
    _fake_tool(project, "cargo-llvm-cov", "#!/bin/sh\n")
    monkeypatch.setenv("STATUS", "101")
    reasons = _blocked_reasons(capsys, coverage_runners.rust_percents)
    assert "Coverage was not measured because tests failed." in reasons


def test_rust_percents_with_coverage_command_missing_installs_it(
    project: Path, monkeypatch: pytest.MonkeyPatch
):
    _fake_tool(project, "cargo", FAKE_CARGO)
    script = '#!/bin/sh\necho "install $*" >> "$CALLS"\n'
    installer = _fake_tool(project, "installer", script)
    monkeypatch.setattr(coverage_runners, "INSTALLER", installer)
    monkeypatch.setenv("REPORT", _rust_report(project, lines=100.0, regions=100.0))
    assert coverage_runners.rust_percents() == {"src/lib.rs": 100.0}
    assert _calls(project)[0] == "install cargo-llvm-cov"


def test_rust_percents_when_coverage_command_cannot_be_installed_exits_2(
    project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    script = "#!/bin/sh\necho 'ERROR: could not install it.' >&2\nexit 1\n"
    installer = _fake_tool(project, "installer", script)
    monkeypatch.setattr(coverage_runners, "INSTALLER", installer)
    reasons = _blocked_reasons(capsys, coverage_runners.rust_percents)
    assert "cargo-llvm-cov is not installed, and installing it failed" in reasons
    assert "could not install it" in reasons


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
    _fake_tool(project, "npx", FAKE_NPX)
    package = {"devDependencies": {runner: "^1.0.0", "typescript": "^5.0.0"}}
    (project / "package.json").write_text(json.dumps(package))
    monkeypatch.setenv("REPORT", _typescript_summary(project, 100, 50))
    assert coverage_runners.typescript_percents() == {"src/order.ts": 50}
    assert _calls(project)[0].startswith(command)


def test_typescript_percents_with_unknown_percent_counts_it_as_covered(
    project: Path, monkeypatch: pytest.MonkeyPatch
):
    _fake_tool(project, "npx", FAKE_NPX)
    (project / "package.json").write_text('{"dependencies": {"vitest": "1"}}')
    monkeypatch.setenv("REPORT", _typescript_summary(project, 80, "Unknown"))
    assert coverage_runners.typescript_percents() == {"src/order.ts": 80}


@pytest.mark.parametrize("package", ['{"devDependencies": {"mocha": "1"}}', "{"])
def test_typescript_percents_without_supported_runner_exits_2(
    project: Path, capsys: pytest.CaptureFixture, package: str
):
    (project / "package.json").write_text(package)
    reasons = _blocked_reasons(capsys, coverage_runners.typescript_percents)
    assert "package.json names neither vitest nor jest" in reasons


def test_typescript_percents_when_runner_cannot_start_exits_2(
    project: Path, capsys: pytest.CaptureFixture
):
    (project / "package.json").write_text('{"devDependencies": {"jest": "1"}}')
    reasons = _blocked_reasons(capsys, coverage_runners.typescript_percents)
    assert "Coverage could not be measured." in reasons
