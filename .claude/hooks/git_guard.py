#!/usr/bin/env python3
"""Git operation safety guards."""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_lib  # noqa: E402
from bash_guard import split_segments  # noqa: E402


def check_stash_destructive(command: str) -> None:
    """Block git stash drop and git stash clear, which delete stashed work."""
    if any(re.match(r"git\s+stash\s+(drop|clear)", seg.strip())
           for seg in split_segments(command)):
        hook_lib.block(
            "'git stash drop/clear' permanently deletes stashed work.",
            "Run 'git stash list' to review stashes before dropping.",
            f"Command: {command[:300]}",
        )


def check_checkout_discard(command: str) -> None:
    """Block git checkout --, which discards uncommitted changes."""
    if any(re.match(r"git\s+checkout\s+--", seg.strip())
           for seg in split_segments(command)):
        hook_lib.block(
            "'git checkout --' discards uncommitted changes permanently.",
            "Use 'git diff' to review changes first, or 'git stash' to save them.",
            f"Command: {command[:300]}",
        )


def check_branch_force_delete(command: str) -> None:
    """Block git branch -D, which deletes a branch that is not merged."""
    if any(re.match(r"git\s+branch\s+-D\b", seg.strip())
           for seg in split_segments(command)):
        hook_lib.block(
            "'git branch -D' force-deletes a branch.",
            "Use 'git branch -d' (safe delete) — it refuses to delete unmerged branches.",
            f"Command: {command[:300]}",
        )


def check_commit_on_main(command: str) -> None:
    """Block a git commit while the current branch is main.

    The branch is MOCK_BRANCH when that is set. Otherwise git reports it for
    the directory in HOOK_ORIG_CWD, or for the current directory.
    """
    if not any(re.match(r"git\s+commit\b", seg.strip())
               for seg in split_segments(command)):
        return
    branch = os.environ.get("MOCK_BRANCH")
    if branch is None:
        cwd = os.environ.get("HOOK_ORIG_CWD", ".")
        result = subprocess.run(
            ["git", "-C", cwd, "branch", "--show-current"],
            capture_output=True, text=True,
        )
        branch = result.stdout.strip()
    if branch == "main":
        hook_lib.block(
            "Cannot commit directly to main.",
            "Run: git checkout main && git pull && git checkout -b <type>/<description>",
            f"Command: {command[:300]}",
        )
