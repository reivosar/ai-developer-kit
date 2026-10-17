"""Tests for post-edit.sh: a file that fails static analysis is sent back to fix."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).parent


def _hooks_with_analysis(tmp_path: Path, status: int) -> Path:
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    shutil.copy(HOOKS_DIR / "post-edit.sh", hooks / "post-edit.sh")
    analysis = hooks / "static-analysis.sh"
    analysis.write_text(
        f'#!/usr/bin/env bash\necho "orders.py:1:1: F401 unused import: $1"\nexit {status}\n'
    )
    analysis.chmod(0o755)
    return hooks


def _run(hooks: Path, file_path: Path) -> subprocess.CompletedProcess:
    payload = json.dumps({"tool_input": {"file_path": str(file_path)}})
    return subprocess.run(
        ["bash", str(hooks / "post-edit.sh")], input=payload,
        capture_output=True, text=True,
    )


def test_post_edit_with_file_that_fails_static_analysis_exits_2(tmp_path: Path):
    edited = tmp_path / "orders.py"
    edited.write_text("import os\n")
    result = _run(_hooks_with_analysis(tmp_path, 1), edited)
    assert result.returncode == 2
    assert f"BLOCKED: static analysis found problems in {edited}" in result.stderr
    assert "F401 unused import" in result.stderr


@pytest.mark.parametrize("exists", [True, False])
def test_post_edit_with_clean_or_missing_file_exits_0(tmp_path: Path, exists: bool):
    edited = tmp_path / "orders.py"
    if exists:
        edited.write_text("VALUE = 1\n")
    result = _run(_hooks_with_analysis(tmp_path, 0), edited)
    assert result.returncode == 0, result.stderr


def _project_with_failing_analysis(tmp_path: Path) -> Path:
    """Return a git project whose .claude/hooks holds post-edit.sh."""
    project = tmp_path / "project"
    (project / ".claude").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(project)], check=True)
    hooks = _hooks_with_analysis(project / ".claude", 1)
    return hooks


@pytest.mark.parametrize("relative", [False, True])
def test_post_edit_with_failing_file_inside_the_project_exits_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, relative: bool
):
    hooks = _project_with_failing_analysis(tmp_path)
    project = hooks.parents[1]
    edited = project / "orders.py"
    edited.write_text("import os\n")
    monkeypatch.chdir(project)
    result = _run(hooks, Path("orders.py") if relative else edited)
    assert result.returncode == 2, result.stderr


def test_post_edit_with_file_outside_the_project_does_not_lint_it(tmp_path: Path):
    hooks = _project_with_failing_analysis(tmp_path)
    note = tmp_path / "memory" / "notes.md"
    note.parent.mkdir()
    note.write_text("# Notes\n")
    result = _run(hooks, note)
    assert result.returncode == 0, result.stderr
    assert "F401" not in result.stderr
