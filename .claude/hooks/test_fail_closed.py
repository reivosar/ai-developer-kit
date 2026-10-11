"""Tests for fail-closed hooks: a blocking hook that cannot finish blocks."""
import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_lib  # noqa: E402

HOOKS_DIR = Path(__file__).parent
BLOCKING_HOOKS = ["pre-bash.py", "pre-write.py", "pre-edit.py", "pre-mcp.py"]


def _run_hook(hook_name: str, stdin_text: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["python3", str(HOOKS_DIR / hook_name)],
        input=stdin_text,
        capture_output=True,
        text=True,
    )


def _feed_stdin(monkeypatch: pytest.MonkeyPatch, text: str) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO(text))


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


def test_run_fail_closed_with_raising_main_exits_2(
    capsys: pytest.CaptureFixture,
):
    def main() -> None:
        raise ValueError("guard state is corrupt")

    with pytest.raises(SystemExit) as blocked:
        hook_lib.run_fail_closed(main)
    assert blocked.value.code == 2
    assert "hook failed: ValueError: guard state is corrupt" in (
        capsys.readouterr().err
    )


def test_run_fail_closed_with_main_exiting_0_keeps_exit_code():
    def main() -> None:
        sys.exit(0)

    with pytest.raises(SystemExit) as allowed:
        hook_lib.run_fail_closed(main)
    assert allowed.value.code == 0


def test_run_fail_closed_with_returning_main_returns_without_blocking():
    assert hook_lib.run_fail_closed(lambda: None) is None


def test_read_hook_input_with_valid_object_returns_object(
    monkeypatch: pytest.MonkeyPatch,
):
    _feed_stdin(monkeypatch, '{"tool_input": {"command": "ls"}}')
    assert hook_lib.read_hook_input() == {"tool_input": {"command": "ls"}}


def test_read_hook_input_without_tool_input_returns_object(
    monkeypatch: pytest.MonkeyPatch,
):
    _feed_stdin(monkeypatch, '{"tool_name": "Bash"}')
    assert hook_lib.read_hook_input() == {"tool_name": "Bash"}


@pytest.mark.parametrize(
    "stdin_text", ["not json", "[1]", '{"tool_input": "oops"}', ""]
)
def test_read_hook_input_with_malformed_input_raises_value_error(
    monkeypatch: pytest.MonkeyPatch, stdin_text: str
):
    _feed_stdin(monkeypatch, stdin_text)
    with pytest.raises(ValueError):
        hook_lib.read_hook_input()
