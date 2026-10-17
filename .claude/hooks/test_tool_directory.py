"""Tests for the tool directory: tools the kit installs into ~/.local/bin are found.

pipx, pip --user, and go install (with the GOBIN install-tool.sh sets) put a
command in ~/.local/bin, which a shell started by Claude Code may not have on
PATH. The scripts and the commit checks add it themselves.
"""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_lib  # noqa: E402

HOOKS_DIR = Path(__file__).parent


def _home_with_tool(tmp_path: Path, tool_stubs, name: str) -> Path:
    """Return a HOME whose .local/bin holds a stand-in for name, off PATH."""
    home = tmp_path / "home"
    tool_stubs.add(name)
    (home / ".local" / "bin").mkdir(parents=True)
    (tool_stubs.commands / name).rename(home / ".local" / "bin" / name)
    return home


def test_static_analysis_with_linter_in_tool_directory_runs_it_without_installing(
    tmp_path: Path, tool_stubs
):
    home = _home_with_tool(tmp_path, tool_stubs, "yamllint")
    document = tmp_path / "settings.yaml"
    document.write_text("key: value\n")
    script = HOOKS_DIR / "static-analysis.sh"
    result = tool_stubs.run_script(script, str(document), HOME=str(home))
    assert result.returncode == 0, result.stderr
    # A stand-in logs two directories above itself, so the moved one logs here.
    moved_calls = (home / ".local" / "calls.log").read_text().splitlines()
    assert moved_calls == [f"yamllint {document}"]
    assert tool_stubs.calls() == []


def test_install_tool_with_tool_in_tool_directory_installs_nothing(
    tmp_path: Path, tool_stubs
):
    home = _home_with_tool(tmp_path, tool_stubs, "revive")
    tool_stubs.add("brew")
    result = tool_stubs.run_script(HOOKS_DIR / "install-tool.sh", "revive", HOME=str(home))
    assert result.returncode == 0, result.stderr
    assert tool_stubs.calls() == []


@pytest.mark.parametrize("path, expected", [
    ("/usr/bin", "/usr/bin:/home/dev/.local/bin"),
    ("/home/dev/.local/bin:/usr/bin", "/home/dev/.local/bin:/usr/bin"),
    ("", "/home/dev/.local/bin"),
])
def test_add_tool_directory_to_path_appends_it_once(
    monkeypatch: pytest.MonkeyPatch, path: str, expected: str
):
    monkeypatch.setenv("HOME", "/home/dev")
    monkeypatch.setenv("PATH", path)
    hook_lib.add_tool_directory_to_path()
    assert os.environ["PATH"] == expected


def test_add_tool_directory_to_path_without_home_leaves_path(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.delenv("HOME", raising=False)
    monkeypatch.setenv("PATH", "/usr/bin")
    hook_lib.add_tool_directory_to_path()
    assert os.environ["PATH"] == "/usr/bin"
