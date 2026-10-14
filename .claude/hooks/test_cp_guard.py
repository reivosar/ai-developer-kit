"""Tests for cp_guard: cp sources, destinations, and options."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cp_guard  # noqa: E402
import hook_lib  # noqa: E402


def _blocked_reasons(capsys: pytest.CaptureFixture, check, command: str) -> str:
    with pytest.raises(SystemExit) as blocked:
        check(command)
    assert blocked.value.code == 2
    return capsys.readouterr().err


@pytest.mark.parametrize(
    "command, option",
    [
        ("cp -f a.txt b.txt", "-f"),
        ("cp --force a.txt b.txt", "--force"),
        ("cp -t dest/ a.txt", "-t"),
        ("cp --target-directory=dest/ a.txt", "--target-directory=dest/"),
    ],
)
def test_check_cp_options_with_forcing_option_exits_2(
    command: str, option: str, capsys: pytest.CaptureFixture
):
    reasons = _blocked_reasons(capsys, cp_guard.check_cp_options, command)
    assert f"cp option '{option}' is not permitted." in reasons


@pytest.mark.parametrize("command", ["cp -r src/ dst/", "git status", "cp 'unbalanced b"])
def test_check_cp_options_with_plain_copy_does_not_block(command: str):
    assert cp_guard.check_cp_options(command) is None


def test_check_cp_source_outside_project_exits_2(capsys: pytest.CaptureFixture):
    reasons = _blocked_reasons(capsys, cp_guard.check_cp_source, "cp /etc/hosts notes.txt")
    assert "cp source '/etc/hosts' is outside the project root" in reasons


@pytest.mark.parametrize("command", ["cp README.md docs/", "cp README.md"])
def test_check_cp_source_inside_project_or_without_destination_does_not_block(
    command: str, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.chdir(hook_lib.REPO_ROOT)
    assert cp_guard.check_cp_source(command) is None


@pytest.mark.parametrize(
    "command", ["cp a.txt .", "cp a.txt", "cp a.txt missing-destination.txt"]
)
def test_check_cp_destination_with_nothing_to_replace_does_not_trash(
    command: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cp_guard.subprocess, "run", _must_not_run)
    assert cp_guard.check_cp_destination(command) is None


def _must_not_run(*arguments: object, **options: object) -> None:
    raise AssertionError("trash.sh was started")


def _trash_result(status: int) -> callable:
    def run(command: list, **options: object) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess(command, status, b"", b"cannot move it")
    return run


def test_check_cp_destination_with_existing_file_moves_it_to_trash(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "notes.txt").write_text("old")
    monkeypatch.setattr(cp_guard.subprocess, "run", _trash_result(0))
    assert cp_guard.check_cp_destination("cp draft.txt notes.txt") is None
    assert "moved existing 'notes.txt' to trash before copy" in capsys.readouterr().err


def test_check_cp_destination_when_trash_fails_exits_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "notes.txt").write_text("old")
    monkeypatch.setattr(cp_guard.subprocess, "run", _trash_result(1))
    reasons = _blocked_reasons(
        capsys, cp_guard.check_cp_destination, "cp draft.txt notes.txt"
    )
    assert "could not trash existing destination 'notes.txt'" in reasons
    assert "cannot move it" in reasons
