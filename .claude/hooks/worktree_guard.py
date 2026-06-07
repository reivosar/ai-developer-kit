#!/usr/bin/env python3
"""Guard: block file writes/edits outside the current git worktree."""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hook_lib import WORKTREES_DIR, block


def _current_worktree() -> "Path | None":
    cwd = Path.cwd().resolve()
    try:
        rel = cwd.relative_to(WORKTREES_DIR)
        return WORKTREES_DIR / rel.parts[0]
    except ValueError:
        return None


def check(file_path: str) -> None:
    if not file_path:
        return
    if os.environ.get("WORKTREE_GUARD_DISABLE"):
        return
    worktree = _current_worktree()
    if worktree is None:
        return
    path = Path(file_path).resolve()
    try:
        path.relative_to(worktree)
    except ValueError:
        block(
            "File changes must stay within the active worktree.",
            f"Active worktree: {worktree}",
            "Run /worktree <type>/<description> to start a new worktree.",
        )
