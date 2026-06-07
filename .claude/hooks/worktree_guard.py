#!/usr/bin/env python3
"""Guard: block file writes/edits outside a git worktree."""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hook_lib import WORKTREES_DIR, block


def check(file_path: str) -> None:
    if not file_path:
        return
    if os.environ.get("WORKTREE_GUARD_DISABLE"):
        return
    path = Path(file_path).resolve()
    try:
        path.relative_to(WORKTREES_DIR)
    except ValueError:
        block(
            "File changes require a worktree.",
            "Run /worktree <type>/<description> first.",
        )
