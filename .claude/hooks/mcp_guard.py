#!/usr/bin/env python3
"""Blocks MCP tool calls that are not in the allowlist."""
import fnmatch
import os
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_lib  # noqa: E402


def _load_allowlist(allowlist_file: Path) -> list[str]:
    try:
        return [line.strip() for line in allowlist_file.read_text().splitlines() if line.strip()]
    except OSError:
        return []


def check_mcp_tool(tool_name: str, allowlist_file: Optional[Path] = None) -> None:
    if not tool_name.startswith("mcp__"):
        return
    if allowlist_file is None:
        allowlist_file = hook_lib.REPO_ROOT / ".claude" / "mcp-allowlist.txt"
    patterns = _load_allowlist(allowlist_file)
    if any(fnmatch.fnmatch(tool_name, p) for p in patterns):
        return
    hook_lib.block(
        f"MCP tool not in allowlist: {tool_name}",
        "Add the tool pattern to .claude/mcp-allowlist.txt to permit it.",
    )
