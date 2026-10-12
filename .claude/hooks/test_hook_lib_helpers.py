"""Tests for the text helpers in hook_lib shared by the guards."""
import io
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_lib  # noqa: E402


def test_tail_lines_returns_the_last_lines_in_order():
    assert hook_lib.tail_lines("first\nsecond\nthird\n", 2) == ["second", "third"]


def test_tail_lines_cuts_a_line_longer_than_the_limit():
    linker_command = "cc " + "-L/toolchain/lib " * 400
    lines = hook_lib.tail_lines(f"error: linking failed\n{linker_command}\n", 5)
    assert lines == ["error: linking failed", linker_command[:hook_lib.MAX_LINE]]


def test_apply_edit_with_repeated_text_replaces_first_occurrence_only():
    edited = hook_lib.apply_edit("a b a", "a", "c", replace_all=False)
    assert edited == "c b a"


def test_apply_edit_with_replace_all_replaces_every_occurrence():
    edited = hook_lib.apply_edit("a b a", "a", "c", replace_all=True)
    assert edited == "c b c"


def test_apply_edit_with_absent_text_returns_text_unchanged():
    assert hook_lib.apply_edit("a b a", "z", "c", replace_all=False) == "a b a"


def test_read_stdin_json_with_valid_object_returns_object(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(sys, "stdin", io.StringIO('{"tool_name": "Bash"}'))
    assert hook_lib.read_stdin_json() == {"tool_name": "Bash"}


def test_read_stdin_json_with_unparsable_input_returns_empty_object(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(sys, "stdin", io.StringIO("not json"))
    assert hook_lib.read_stdin_json() == {}


def test_find_repo_root_with_relative_git_directory_returns_toplevel(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    git_outputs = iter([".git\n", f"{tmp_path}\n"])
    monkeypatch.setattr(
        hook_lib.subprocess, "check_output",
        lambda *arguments, **options: next(git_outputs),
    )
    assert hook_lib._find_repo_root() == tmp_path.resolve()


def test_read_text_with_utf8_file_returns_content(tmp_path: Path):
    document = tmp_path / "guide.md"
    document.write_text("first\nsecond\n")
    assert hook_lib.read_text(str(document)) == "first\nsecond\n"


def test_read_text_with_non_utf8_file_returns_text_without_raising(
    tmp_path: Path,
):
    document = tmp_path / "legacy.md"
    document.write_bytes(b"caf\xe9\n")
    assert hook_lib.read_text(str(document)).startswith("caf")
