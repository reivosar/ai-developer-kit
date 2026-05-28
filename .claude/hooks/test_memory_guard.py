"""Tests for memory_guard.py — MEMORY.md line count enforcement."""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from memory_guard import check_edit, check_write


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
