"""Tests for the fail-closed handlers: fail_closed, run_fail_closed, read_hook_input."""
import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fail_closed  # noqa: E402
import hook_lib  # noqa: E402

HOOKS_DIR = Path(__file__).parent


def _feed_stdin(monkeypatch: pytest.MonkeyPatch, text: str) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO(text))


def test_run_entry_point_runs_the_named_script_as_main(tmp_path: Path):
    marker = tmp_path / "ran.txt"
    script = tmp_path / "probe.py"
    script.write_text(
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text(__name__)\n"
    )
    fail_closed.run_entry_point("probe.py", directory=tmp_path)
    assert marker.read_text() == "__main__"


def test_install_replaces_the_uncaught_error_handler(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(sys, "excepthook", sys.__excepthook__)
    fail_closed.install()
    assert sys.excepthook is fail_closed.block_uncaught


def test_settings_start_every_blocking_python_hook_through_the_launcher():
    settings = json.loads((HOOKS_DIR.parent / "settings.json").read_text())
    commands = [
        hook["command"]
        for entry in settings["hooks"]["PreToolUse"] for hook in entry["hooks"]
        if hook["command"].startswith("python3 ")
    ]
    launcher = "python3 .claude/hooks/run-hook.py "
    assert commands == [
        launcher + hook_name
        for hook_name in [
            "pre-bash.py", "pre-write.py", "memory_guard.py", "pre-edit.py",
            "pre-mcp.py",
        ]
    ]


def test_install_makes_an_uncaught_error_exit_2(tmp_path: Path):
    script = tmp_path / "probe.py"
    script.write_text(
        f"import sys\nsys.path.insert(0, {str(HOOKS_DIR)!r})\n"
        "import fail_closed\nfail_closed.install()\n"
        "raise ValueError('guard state is corrupt')\n"
    )
    result = subprocess.run(
        [sys.executable, str(script)], capture_output=True, text=True
    )
    assert result.returncode == 2
    assert "BLOCKED: hook failed: ValueError: guard state is corrupt" in result.stderr


@pytest.mark.parametrize("status", [0, 2])
def test_install_leaves_a_deliberate_exit_code_alone(tmp_path: Path, status: int):
    script = tmp_path / "probe.py"
    script.write_text(
        f"import sys\nsys.path.insert(0, {str(HOOKS_DIR)!r})\n"
        f"import fail_closed\nfail_closed.install()\nsys.exit({status})\n"
    )
    result = subprocess.run([sys.executable, str(script)], capture_output=True)
    assert result.returncode == status


def test_block_uncaught_prints_the_error_and_leaves_with_2(
    capsys: pytest.CaptureFixture,
):
    codes = []
    fail_closed.block_uncaught(
        ValueError, ValueError("guard state is corrupt"), None, leave=codes.append
    )
    assert codes == [2]
    assert "BLOCKED: hook failed: ValueError: guard state is corrupt" in (
        capsys.readouterr().err
    )


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
