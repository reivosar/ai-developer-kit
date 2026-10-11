"""Tests for commit_guard: pre-commit checks on the staged change."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import commit_guard  # noqa: E402

COMMIT = "git commit -m 'add orders'"
CLEAN_LINE = "total = 1\n"
# Built at runtime so this file does not trip the checks it tests.
CREDENTIAL_LINE = "pass" + 'word = "hunter2hunter2"\n'
EMOJI_LINE = "status = 'done " + chr(0x1F600) + "'\n"
TRAILING_SPACE_LINE = "total = 1" + " " + "\n"


def _init(directory: Path, branch: str) -> Path:
    subprocess.run(
        ["git", "init", "-q", "-b", branch, str(directory)], check=True
    )
    return directory


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    return _init(tmp_path, "feat/orders")


def _stage(project: Path, name: str, content: str) -> None:
    (project / name).write_text(content)
    subprocess.run(["git", "-C", str(project), "add", name], check=True)


def _blocked_reasons(capsys: pytest.CaptureFixture) -> str:
    with pytest.raises(SystemExit) as blocked:
        commit_guard.check_pre_commit(COMMIT)
    assert blocked.value.code == 2
    return capsys.readouterr().err


def test_check_pre_commit_with_clean_change_does_not_block(project: Path):
    _stage(project, "orders.py", CLEAN_LINE)
    assert commit_guard.check_pre_commit(COMMIT) is None


def test_check_pre_commit_with_credential_exits_2(
    project: Path, capsys: pytest.CaptureFixture
):
    _stage(project, "orders.py", CREDENTIAL_LINE)
    assert "Potential secret detected" in _blocked_reasons(capsys)


def test_check_pre_commit_with_credential_on_example_line_does_not_block(
    project: Path,
):
    _stage(project, "orders.py", CREDENTIAL_LINE.strip() + "  # .example\n")
    assert commit_guard.check_pre_commit(COMMIT) is None


def test_check_pre_commit_with_unprefixed_branch_exits_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
):
    monkeypatch.chdir(_init(tmp_path, "orders"))
    _stage(tmp_path, "orders.py", CLEAN_LINE)
    assert "does not follow the required prefix" in _blocked_reasons(capsys)


def test_check_pre_commit_on_main_branch_skips_branch_name_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.chdir(_init(tmp_path, "main"))
    _stage(tmp_path, "orders.py", CLEAN_LINE)
    assert commit_guard.check_pre_commit(COMMIT) is None


def test_check_pre_commit_with_trailing_whitespace_exits_2(
    project: Path, capsys: pytest.CaptureFixture
):
    _stage(project, "orders.py", TRAILING_SPACE_LINE)
    assert "Trailing whitespace found" in _blocked_reasons(capsys)


def test_check_pre_commit_with_env_file_staged_exits_2(
    project: Path, capsys: pytest.CaptureFixture
):
    _stage(project, ".env", "REGION=tokyo\n")
    assert "'.env' files must not be committed" in _blocked_reasons(capsys)


def test_check_pre_commit_with_env_example_staged_does_not_block(
    project: Path,
):
    _stage(project, ".env.example", "REGION=tokyo\n")
    assert commit_guard.check_pre_commit(COMMIT) is None


def test_check_pre_commit_with_emoji_exits_2(
    project: Path, capsys: pytest.CaptureFixture
):
    _stage(project, "orders.py", EMOJI_LINE)
    assert "Emoji detected" in _blocked_reasons(capsys)


def test_check_pre_commit_with_two_violations_reports_both(
    project: Path, capsys: pytest.CaptureFixture
):
    _stage(project, "orders.py", CREDENTIAL_LINE + EMOJI_LINE)
    reasons = _blocked_reasons(capsys)
    assert "Potential secret detected" in reasons
    assert "Emoji detected" in reasons


def test_check_pre_commit_with_other_command_does_not_block(project: Path):
    _stage(project, "orders.py", CREDENTIAL_LINE)
    assert commit_guard.check_pre_commit("git status") is None


def test_check_pre_commit_with_nothing_staged_does_not_block(project: Path):
    assert commit_guard.check_pre_commit(COMMIT) is None


@pytest.mark.parametrize(
    "command",
    [COMMIT, "cd service && git commit -m 'x'", "git add a; git commit"],
)
def test_is_commit_with_commit_command_returns_true(command: str):
    assert commit_guard.is_commit(command) is True


@pytest.mark.parametrize(
    "command", ["git status", "git log --grep 'git commit'", "echo git commit"]
)
def test_is_commit_with_other_command_returns_false(command: str):
    assert commit_guard.is_commit(command) is False


def test_staged_files_with_two_staged_files_returns_both(project: Path):
    _stage(project, "orders.py", CLEAN_LINE)
    _stage(project, "refunds.py", CLEAN_LINE)
    assert commit_guard.staged_files() == ["orders.py", "refunds.py"]
