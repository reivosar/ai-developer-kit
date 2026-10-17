"""Tests for fail-closed hooks: a blocking hook that cannot finish blocks."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).parent
BLOCKING_HOOKS = ["pre-bash.py", "pre-write.py", "pre-edit.py", "pre-mcp.py"]
# memory_guard.py also blocks a Write. It is imported by its own tests, so it
# does not install the handler itself; started through run-hook.py it is
# covered like the others.
HOOKS_THAT_BLOCK = BLOCKING_HOOKS + ["memory_guard.py"]
BROKEN_MODULE = 'raise RuntimeError("guard module is broken")\n'
WRITE = json.dumps(
    {"tool_name": "Write", "tool_input": {"file_path": "notes.txt", "content": "x"}}
)


def _run_hook(hook_name: str, stdin_text: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HOOKS_DIR / hook_name)],
        input=stdin_text,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize("hook_name", BLOCKING_HOOKS)
def test_blocking_hook_with_unparsable_input_exits_2(hook_name: str):
    result = _run_hook(hook_name, "not json")
    assert result.returncode == 2, result.stderr
    assert "hook failed" in result.stderr


@pytest.mark.parametrize("hook_name", BLOCKING_HOOKS)
def test_blocking_hook_with_non_object_input_exits_2(hook_name: str):
    result = _run_hook(hook_name, "[1]")
    assert result.returncode == 2, result.stderr
    assert "hook failed" in result.stderr


@pytest.mark.parametrize("hook_name", BLOCKING_HOOKS)
def test_blocking_hook_with_non_object_tool_input_exits_2(hook_name: str):
    payload = json.dumps({"tool_name": "Probe", "tool_input": "oops"})
    result = _run_hook(hook_name, payload)
    assert result.returncode == 2, result.stderr
    assert "hook failed" in result.stderr


def _kit_copy(project: Path) -> Path:
    """Copy the kit's hooks and settings into project and return the hooks."""
    hooks = project / ".claude" / "hooks"
    skipped = shutil.ignore_patterns("__pycache__", "test_*")
    shutil.copytree(HOOKS_DIR, hooks, ignore=skipped)
    shutil.copy(HOOKS_DIR.parent / "settings.json", project / ".claude")
    return hooks


def _run_copied_hook(hooks: Path, hook_name: str, payload: str):
    environment = {**os.environ, "RATE_LIMIT_DISABLE": "1"}
    return subprocess.run(
        [sys.executable, str(hooks / hook_name)], input=payload, capture_output=True,
        text=True, env=environment, cwd=hooks.parents[1],
    )


@pytest.mark.parametrize("hook_name", BLOCKING_HOOKS)
def test_blocking_hook_when_shared_library_cannot_load_exits_2(
    tmp_path: Path, hook_name: str
):
    hooks = _kit_copy(tmp_path)
    (hooks / "hook_lib.py").write_text(BROKEN_MODULE)
    result = _run_copied_hook(hooks, hook_name, WRITE)
    assert result.returncode == 2, result.stderr
    assert "hook failed: RuntimeError: guard module is broken" in result.stderr


@pytest.mark.parametrize("hook_name", HOOKS_THAT_BLOCK)
def test_launcher_when_shared_library_cannot_load_exits_2(
    tmp_path: Path, hook_name: str
):
    hooks = _kit_copy(tmp_path)
    (hooks / "hook_lib.py").write_text(BROKEN_MODULE)
    result = _launch(hooks, hook_name, WRITE)
    assert result.returncode == 2, result.stderr
    assert "hook failed: RuntimeError: guard module is broken" in result.stderr


@pytest.mark.parametrize("hook_name", BLOCKING_HOOKS)
def test_blocking_hook_when_guard_module_has_syntax_error_exits_2(
    tmp_path: Path, hook_name: str
):
    hooks = _kit_copy(tmp_path)
    (hooks / "audit_log.py").write_text("def record(:\n")
    result = _run_copied_hook(hooks, hook_name, WRITE)
    assert result.returncode == 2, result.stderr
    assert "hook failed: SyntaxError" in result.stderr


@pytest.mark.parametrize("command, status", [("ls", 0), ("node --version", 2)])
def test_pre_bash_outside_a_git_repository_still_enforces_the_allow_list(
    tmp_path: Path, command: str, status: int
):
    hooks = _kit_copy(tmp_path)
    payload = json.dumps({"tool_input": {"command": command}})
    result = _run_copied_hook(hooks, "pre-bash.py", payload)
    assert result.returncode == status, result.stderr


def _launch(hooks: Path, hook_name: str, payload: str):
    environment = {**os.environ, "RATE_LIMIT_DISABLE": "1"}
    command = [sys.executable, str(hooks / "run-hook.py"), hook_name]
    return subprocess.run(
        command, input=payload, capture_output=True, text=True, env=environment,
        cwd=hooks.parents[1],
    )


@pytest.mark.parametrize("hook_name", HOOKS_THAT_BLOCK)
def test_launcher_when_entry_point_has_syntax_error_exits_2(
    tmp_path: Path, hook_name: str
):
    hooks = _kit_copy(tmp_path)
    (hooks / hook_name).write_text("def main(:\n")
    result = _launch(hooks, hook_name, WRITE)
    assert result.returncode == 2, result.stderr
    assert "hook failed: SyntaxError" in result.stderr


@pytest.mark.parametrize("command, status", [("ls", 0), ("node --version", 2)])
def test_launcher_runs_the_entry_point_and_keeps_its_exit_code(
    tmp_path: Path, command: str, status: int
):
    hooks = _kit_copy(tmp_path)
    payload = json.dumps({"tool_input": {"command": command}})
    result = _launch(hooks, "pre-bash.py", payload)
    assert result.returncode == status, result.stderr


@pytest.mark.parametrize("hook_name", ["", "no-such-hook.py"])
def test_launcher_without_an_entry_point_it_can_run_exits_2(
    tmp_path: Path, hook_name: str
):
    hooks = _kit_copy(tmp_path)
    arguments = [hook_name] if hook_name else []
    result = subprocess.run(
        [sys.executable, str(hooks / "run-hook.py"), *arguments],
        input=WRITE, capture_output=True, text=True,
    )
    assert result.returncode == 2, result.stderr
    assert "hook failed" in result.stderr
