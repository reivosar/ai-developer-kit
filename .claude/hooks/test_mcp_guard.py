"""Tests for mcp_guard.check_mcp_tool."""
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

HOOKS_DIR = str(Path(__file__).resolve().parent)


def _exit_code(tool_name: str, allowlist_content: str | None) -> int:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        if allowlist_content is not None:
            f.write(allowlist_content)
        tmp_path = f.name
    script = (
        f"import sys; sys.path.insert(0, {HOOKS_DIR!r})\n"
        f"from pathlib import Path\n"
        f"import mcp_guard\n"
        f"mcp_guard.check_mcp_tool({tool_name!r}, allowlist_file=Path({tmp_path!r}))\n"
    )
    return subprocess.run([sys.executable, "-c", script], capture_output=True).returncode


def test_check_mcp_tool_with_empty_allowlist_blocks_mcp_tool():
    assert _exit_code("mcp__google_drive__list", "") == 2


def test_check_mcp_tool_with_listed_exact_pattern_passes():
    assert _exit_code("mcp__google_drive__list", "mcp__google_drive__list\n") == 0


def test_check_mcp_tool_with_listed_wildcard_pattern_passes():
    assert _exit_code("mcp__google_drive__list", "mcp__google_drive__*\n") == 0


def test_check_mcp_tool_with_unlisted_tool_blocks():
    assert _exit_code("mcp__slack__send", "mcp__google_drive__*\n") == 2


def test_check_mcp_tool_with_non_mcp_tool_name_passes():
    assert _exit_code("Bash", "") == 0


def test_check_mcp_tool_with_absent_allowlist_blocks_mcp_tool():
    script = (
        f"import sys; sys.path.insert(0, {HOOKS_DIR!r})\n"
        f"from pathlib import Path\n"
        f"import mcp_guard\n"
        f"mcp_guard.check_mcp_tool('mcp__absent__tool',"
        f" allowlist_file=Path('/nonexistent/path.txt'))\n"
    )
    assert subprocess.run([sys.executable, "-c", script], capture_output=True).returncode == 2


def test_check_mcp_tool_with_multiple_patterns_passes_matching_tool():
    allowlist = "mcp__google_drive__*\nmcp__github__*\n"
    assert _exit_code("mcp__github__create_issue", allowlist) == 0


def test_check_mcp_tool_with_multiple_patterns_blocks_unlisted_tool():
    allowlist = "mcp__google_drive__*\nmcp__github__*\n"
    assert _exit_code("mcp__slack__send", allowlist) == 2


def test_check_mcp_tool_with_unreadable_allowlist_blocks_mcp_tool(tmp_path):
    # A directory path instead of a file causes IsADirectoryError (OSError subclass)
    script = (
        f"import sys; sys.path.insert(0, {HOOKS_DIR!r})\n"
        f"from pathlib import Path\n"
        f"import mcp_guard\n"
        f"mcp_guard.check_mcp_tool('mcp__test__tool',"
        f" allowlist_file=Path({str(tmp_path)!r}))\n"
    )
    assert subprocess.run([sys.executable, "-c", script], capture_output=True).returncode == 2
