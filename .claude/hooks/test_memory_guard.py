"""Tests for memory_guard.py — MEMORY.md line count enforcement."""
import io
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import memory_guard  # noqa: E402
from memory_guard import check_edit, check_write  # noqa: E402

MEMORY_FILE = "/some/memory/MEMORY.md"


def _feed_stdin(monkeypatch: pytest.MonkeyPatch, payload: dict) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))


def test_check_edit_with_missing_memory_file_does_not_block(tmp_path: Path):
    missing = tmp_path / "memory" / "MEMORY.md"
    assert check_edit(str(missing)) is None


def test_main_with_write_over_limit_exits_2(monkeypatch: pytest.MonkeyPatch):
    tool_input = {"file_path": MEMORY_FILE, "content": make_content(201)}
    _feed_stdin(monkeypatch, {"tool_name": "Write", "tool_input": tool_input})
    with pytest.raises(SystemExit) as blocked:
        memory_guard.main()
    assert blocked.value.code == 2


def test_main_with_edit_over_limit_exits_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    memory_file = tmp_path / "memory" / "MEMORY.md"
    memory_file.parent.mkdir()
    memory_file.write_text(make_content(201))
    tool_input = {"file_path": str(memory_file)}
    _feed_stdin(monkeypatch, {"tool_name": "Edit", "tool_input": tool_input})
    with pytest.raises(SystemExit) as reported:
        memory_guard.main()
    assert reported.value.code == 1


def test_main_with_other_tool_does_not_block(monkeypatch: pytest.MonkeyPatch):
    tool_input = {"file_path": MEMORY_FILE}
    _feed_stdin(monkeypatch, {"tool_name": "Read", "tool_input": tool_input})
    assert memory_guard.main() is None


def make_content(lines: int) -> str:
    return "\n".join(f"line {i}" for i in range(lines))


class TestCheckWrite:
    def test_write_memory_md_under_limit_allows(self):
        check_write("/some/memory/MEMORY.md", make_content(199))

    def test_write_memory_md_at_limit_allows(self):
        check_write("/some/memory/MEMORY.md", make_content(200))

    def test_write_memory_md_over_limit_blocks(self):
        with pytest.raises(SystemExit):
            check_write("/some/memory/MEMORY.md", make_content(201))

    def test_write_non_memory_file_over_limit_allows(self):
        check_write("/some/other/file.md", make_content(201))


class TestCheckEdit:
    def test_edit_memory_md_at_limit_allows(self, tmp_path: Path):
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        f = memory_dir / "MEMORY.md"
        f.write_text(make_content(200))
        check_edit(str(f))

    def test_edit_memory_md_over_limit_exits_error(self, tmp_path: Path):
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        f = memory_dir / "MEMORY.md"
        f.write_text(make_content(201))
        with pytest.raises(SystemExit) as exc_info:
            check_edit(str(f))
        assert exc_info.value.code != 0

    def test_edit_non_memory_file_over_limit_allows(self, tmp_path: Path):
        f = tmp_path / "other.md"
        f.write_text(make_content(201))
        check_edit(str(f))
