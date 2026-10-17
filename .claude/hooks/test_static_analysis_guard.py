"""Tests for static_analysis_guard: a commit is linted before it is made."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import static_analysis_guard  # noqa: E402

HOOKS_DIR = Path(__file__).parent
COMMIT = "git commit -m 'add discount'"
UNUSED_IMPORT = "import os\n"
CLEAN_MODULE = '"""Values."""\n\nVALUE = 1\n'


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    subprocess.run(
        ["git", "init", "-q", "-b", "feat/discount", str(tmp_path)], check=True
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("STATIC_ANALYSIS_GUARD_DISABLE", raising=False)
    return tmp_path


def _stage(project: Path, name: str, content: str) -> None:
    (project / name).write_text(content)
    subprocess.run(["git", "-C", str(project), "add", name], check=True)


def _analysis(project: Path, status: int) -> Path:
    script = project / "static-analysis.sh"
    script.write_text(
        "#!/bin/sh\n"
        f'echo "$STATIC_ANALYSIS_MODE" >> "{project}/analysis.log"\n'
        "echo 'orders.py:1:1: F401 os imported but unused'\n"
        f"exit {status}\n"
    )
    script.chmod(0o755)
    return script


def _blocked_reasons(capsys: pytest.CaptureFixture) -> str:
    with pytest.raises(SystemExit) as blocked:
        static_analysis_guard.check_staged_files(COMMIT)
    assert blocked.value.code == 2
    return capsys.readouterr().err


def test_check_staged_files_with_finding_exits_2_and_shows_it(
    project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    _stage(project, "orders.py", UNUSED_IMPORT)
    monkeypatch.setattr(static_analysis_guard, "SCRIPT", _analysis(project, 1))
    reasons = _blocked_reasons(capsys)
    assert "Static analysis found problems in the staged files." in reasons
    assert "orders.py:1:1: F401 os imported but unused" in reasons


def test_check_staged_files_runs_analysis_on_staged_files_only(
    project: Path, monkeypatch: pytest.MonkeyPatch
):
    _stage(project, "orders.py", CLEAN_MODULE)
    monkeypatch.setattr(static_analysis_guard, "SCRIPT", _analysis(project, 0))
    assert static_analysis_guard.check_staged_files(COMMIT) is None
    assert (project / "analysis.log").read_text() == "staged\n"


@pytest.mark.parametrize("command", ["git status", "git log --grep 'git commit'"])
def test_check_staged_files_with_other_command_does_not_run_analysis(
    project: Path, monkeypatch: pytest.MonkeyPatch, command: str
):
    _stage(project, "orders.py", UNUSED_IMPORT)
    monkeypatch.setattr(static_analysis_guard, "SCRIPT", _analysis(project, 1))
    assert static_analysis_guard.check_staged_files(command) is None
    assert not (project / "analysis.log").exists()


def test_check_staged_files_with_nothing_staged_does_not_run_analysis(
    project: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(static_analysis_guard, "SCRIPT", _analysis(project, 1))
    assert static_analysis_guard.check_staged_files(COMMIT) is None
    assert not (project / "analysis.log").exists()


def test_check_staged_files_with_guard_disabled_does_not_run_analysis(
    project: Path, monkeypatch: pytest.MonkeyPatch
):
    _stage(project, "orders.py", UNUSED_IMPORT)
    monkeypatch.setattr(static_analysis_guard, "SCRIPT", _analysis(project, 1))
    monkeypatch.setenv("STATIC_ANALYSIS_GUARD_DISABLE", "1")
    assert static_analysis_guard.check_staged_files(COMMIT) is None
    assert not (project / "analysis.log").exists()


def test_check_staged_files_when_analysis_cannot_run_exits_2(
    project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    _stage(project, "orders.py", CLEAN_MODULE)
    missing = project / "no-such-script.sh"
    monkeypatch.setattr(static_analysis_guard, "SCRIPT", missing)
    assert "Static analysis could not run." in _blocked_reasons(capsys)


def _commit_through_pre_bash() -> subprocess.CompletedProcess:
    payload = json.dumps({"tool_input": {"command": COMMIT}})
    env = {
        **os.environ, "RATE_LIMIT_DISABLE": "1", "COVERAGE_GUARD_DISABLE": "1",
    }
    return subprocess.run(
        [sys.executable, str(HOOKS_DIR / "pre-bash.py")],
        input=payload, capture_output=True, text=True, env=env,
    )


def test_main_of_pre_bash_with_commit_of_file_that_fails_lint_exits_2(project: Path):
    _stage(project, "orders.py", UNUSED_IMPORT)
    result = _commit_through_pre_bash()
    assert result.returncode == 2, result.stderr
    assert "F401" in result.stderr


def test_main_of_pre_bash_with_commit_of_clean_file_exits_0(project: Path):
    _stage(project, "orders.py", CLEAN_MODULE)
    result = _commit_through_pre_bash()
    assert result.returncode == 0, result.stderr
