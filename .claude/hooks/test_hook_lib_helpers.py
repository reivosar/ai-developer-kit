"""Tests for the text helpers in hook_lib shared by the guards."""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_lib  # noqa: E402


def test_apply_edit_with_repeated_text_replaces_first_occurrence_only():
    edited = hook_lib.apply_edit("a b a", "a", "c", replace_all=False)
    assert edited == "c b a"


def test_apply_edit_with_replace_all_replaces_every_occurrence():
    edited = hook_lib.apply_edit("a b a", "a", "c", replace_all=True)
    assert edited == "c b c"


def test_apply_edit_with_absent_text_returns_text_unchanged():
    assert hook_lib.apply_edit("a b a", "z", "c", replace_all=False) == "a b a"


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
