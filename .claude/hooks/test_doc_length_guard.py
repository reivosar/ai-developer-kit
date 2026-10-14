"""Tests for doc_length_guard: Markdown documents must fit the line limit."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import doc_length_guard  # noqa: E402

HOOKS_DIR = Path(__file__).parent
LIMIT = doc_length_guard.LINE_LIMIT
ONE_LINE = "line\n"
TWO_LINES = "line\nline\n"


def _write_document(directory: Path, line_count: int) -> Path:
    document = directory / "guide.md"
    document.write_text(ONE_LINE * line_count)
    return document


def _run_hook(
    hook_name: str, tool_input: dict, **extra_env: str
) -> subprocess.CompletedProcess:
    env = {**os.environ, "WORKTREE_GUARD_DISABLE": "1", **extra_env}
    return subprocess.run(
        [sys.executable, str(HOOKS_DIR / hook_name)],
        input=json.dumps({"tool_input": tool_input}),
        capture_output=True,
        text=True,
        env=env,
    )


def test_check_write_with_markdown_over_limit_exits_2() -> None:
    with pytest.raises(SystemExit) as blocked:
        doc_length_guard.check_write("docs/guide.md", ONE_LINE * (LIMIT + 1))
    assert blocked.value.code == 2


def test_check_write_with_markdown_at_limit_does_not_block() -> None:
    at_limit = ONE_LINE * LIMIT
    assert doc_length_guard.check_write("docs/guide.md", at_limit) is None


def test_check_write_with_non_markdown_over_limit_does_not_block() -> None:
    over_limit = ONE_LINE * (LIMIT + 1)
    assert doc_length_guard.check_write("src/data.py", over_limit) is None


def test_check_write_with_guard_disabled_does_not_block(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DOC_LENGTH_GUARD_DISABLE", "1")
    over_limit = ONE_LINE * (LIMIT + 1)
    assert doc_length_guard.check_write("docs/guide.md", over_limit) is None


def test_check_edit_growing_markdown_past_limit_exits_2(
    tmp_path: Path,
) -> None:
    document = _write_document(tmp_path, LIMIT)
    with pytest.raises(SystemExit) as blocked:
        doc_length_guard.check_edit(str(document), ONE_LINE, TWO_LINES)
    assert blocked.value.code == 2


def test_check_edit_growing_markdown_to_limit_does_not_block(
    tmp_path: Path,
) -> None:
    document = _write_document(tmp_path, LIMIT - 1)
    outcome = doc_length_guard.check_edit(str(document), ONE_LINE, TWO_LINES)
    assert outcome is None


def test_check_edit_shrinking_over_limit_markdown_does_not_block(
    tmp_path: Path,
) -> None:
    document = _write_document(tmp_path, LIMIT + 10)
    outcome = doc_length_guard.check_edit(str(document), TWO_LINES, ONE_LINE)
    assert outcome is None


def test_check_edit_with_replace_all_growing_past_limit_exits_2(
    tmp_path: Path,
) -> None:
    document = _write_document(tmp_path, LIMIT // 2 + 1)
    with pytest.raises(SystemExit) as blocked:
        doc_length_guard.check_edit(
            str(document), ONE_LINE, TWO_LINES, replace_all=True
        )
    assert blocked.value.code == 2


def test_check_edit_with_missing_file_does_not_block(tmp_path: Path) -> None:
    absent = str(tmp_path / "absent.md")
    outcome = doc_length_guard.check_edit(absent, ONE_LINE, TWO_LINES)
    assert outcome is None


def test_check_edit_with_non_utf8_markdown_does_not_block(
    tmp_path: Path,
) -> None:
    document = tmp_path / "legacy.md"
    document.write_bytes(b"caf\xe9\n")
    outcome = doc_length_guard.check_edit(str(document), "caf", "tea")
    assert outcome is None


def test_pre_write_with_markdown_over_limit_exits_2() -> None:
    probe = HOOKS_DIR / "_doc_length_probe.md"
    tool_input = {"file_path": str(probe), "content": ONE_LINE * (LIMIT + 1)}
    result = _run_hook("pre-write.py", tool_input)
    assert result.returncode == 2, result.stderr
    assert "document limit" in result.stderr


def test_pre_edit_growing_markdown_past_limit_exits_2(tmp_path: Path) -> None:
    document = _write_document(tmp_path, LIMIT)
    tool_input = {
        "file_path": str(document),
        "old_string": ONE_LINE,
        "new_string": TWO_LINES,
    }
    result = _run_hook(
        "pre-edit.py", tool_input, ANOMALY_PATH_ESCAPE_DISABLE="1"
    )
    assert result.returncode == 2, result.stderr
    assert "document limit" in result.stderr
