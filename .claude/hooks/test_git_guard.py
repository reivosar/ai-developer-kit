"""Tests for git_guard: destructive git commands and commits on main."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import git_guard  # noqa: E402

COMMIT = "git commit -m 'add order export'"


@pytest.fixture(autouse=True)
def real_branch_lookup(monkeypatch: pytest.MonkeyPatch) -> None:
    # The branch must come from the repository each test names, never from
    # the checkout the suite happens to run in.
    monkeypatch.delenv("MOCK_BRANCH", raising=False)
    monkeypatch.delenv("HOOK_ORIG_CWD", raising=False)


def _repository_on(branch: str, directory: Path) -> Path:
    subprocess.run(["git", "init", "-q", "-b", branch, str(directory)], check=True)
    return directory


@pytest.mark.parametrize("command", ["git stash drop", "git stash clear"])
def test_check_stash_destructive_with_drop_or_clear_exits_2(command: str):
    with pytest.raises(SystemExit) as blocked:
        git_guard.check_stash_destructive(command)
    assert blocked.value.code == 2


@pytest.mark.parametrize(
    "command", ['git commit -m "git stash drop"', "git stash list"]
)
def test_check_stash_destructive_with_safe_command_does_not_block(command: str):
    assert git_guard.check_stash_destructive(command) is None


def test_check_checkout_discard_with_double_dash_exits_2():
    with pytest.raises(SystemExit) as blocked:
        git_guard.check_checkout_discard("git checkout -- README.md")
    assert blocked.value.code == 2


@pytest.mark.parametrize(
    "command", ['git commit -m "git checkout -- file"', "git checkout main"]
)
def test_check_checkout_discard_with_safe_command_does_not_block(command: str):
    assert git_guard.check_checkout_discard(command) is None


def test_check_branch_force_delete_with_capital_d_exits_2():
    with pytest.raises(SystemExit) as blocked:
        git_guard.check_branch_force_delete("git branch -D old")
    assert blocked.value.code == 2


@pytest.mark.parametrize(
    "command", ['git commit -m "git branch -D old"', "git branch -d old"]
)
def test_check_branch_force_delete_with_safe_command_does_not_block(command: str):
    assert git_guard.check_branch_force_delete(command) is None


@pytest.mark.parametrize("command", ["git push origin HEAD", "git push -u origin HEAD"])
def test_check_push_on_main_with_mock_branch_main_exits_2(
    command: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    monkeypatch.setenv("MOCK_BRANCH", "main")
    with pytest.raises(SystemExit) as blocked:
        git_guard.check_push_on_main(command)
    assert blocked.value.code == 2
    assert "Cannot push main." in capsys.readouterr().err


def test_check_push_on_main_with_mock_branch_feature_does_not_block(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("MOCK_BRANCH", "feat/order-export")
    assert git_guard.check_push_on_main("git push -u origin HEAD") is None


def test_check_push_on_main_with_command_other_than_push_does_not_block(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("MOCK_BRANCH", "main")
    assert git_guard.check_push_on_main("git status") is None


def test_check_push_on_main_in_repository_on_main_exits_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("HOOK_ORIG_CWD", str(_repository_on("main", tmp_path)))
    with pytest.raises(SystemExit) as blocked:
        git_guard.check_push_on_main("git push origin HEAD")
    assert blocked.value.code == 2


def test_check_commit_on_main_with_mock_branch_main_exits_2(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("MOCK_BRANCH", "main")
    with pytest.raises(SystemExit) as blocked:
        git_guard.check_commit_on_main(COMMIT)
    assert blocked.value.code == 2


def test_check_commit_on_main_with_mock_branch_feature_does_not_block(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("MOCK_BRANCH", "feat/order-export")
    assert git_guard.check_commit_on_main(COMMIT) is None


def test_check_commit_on_main_with_command_other_than_commit_does_not_block(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("MOCK_BRANCH", "main")
    assert git_guard.check_commit_on_main("git status") is None


def test_check_commit_on_main_in_repository_on_main_exits_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("HOOK_ORIG_CWD", str(_repository_on("main", tmp_path)))
    with pytest.raises(SystemExit) as blocked:
        git_guard.check_commit_on_main(COMMIT)
    assert blocked.value.code == 2


def test_check_commit_on_main_in_repository_on_main_names_command_in_message(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
):
    monkeypatch.setenv("HOOK_ORIG_CWD", str(_repository_on("main", tmp_path)))
    with pytest.raises(SystemExit):
        git_guard.check_commit_on_main(COMMIT)
    message = capsys.readouterr().err
    assert "Cannot commit directly to main." in message
    assert f"Command: {COMMIT}" in message


def test_check_commit_on_main_in_repository_on_feature_branch_does_not_block(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    repository = _repository_on("feat/order-export", tmp_path)
    monkeypatch.setenv("HOOK_ORIG_CWD", str(repository))
    assert git_guard.check_commit_on_main(COMMIT) is None


def test_check_commit_on_main_without_hook_cwd_reads_current_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.chdir(_repository_on("main", tmp_path))
    with pytest.raises(SystemExit) as blocked:
        git_guard.check_commit_on_main(COMMIT)
    assert blocked.value.code == 2


def test_check_commit_on_main_without_hook_cwd_on_feature_branch_does_not_block(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.chdir(_repository_on("feat/order-export", tmp_path))
    assert git_guard.check_commit_on_main(COMMIT) is None
