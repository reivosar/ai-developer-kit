#!/usr/bin/env python3
"""Git operation safety guards; git_option_guard checks the options."""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_lib  # noqa: E402
from bash_guard import command_words, split_segments  # noqa: E402


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


def check_git_subcommand(command: str, allow_patterns: list[str]) -> None:
    """Block a git subcommand that the allow list does not name.

    A pattern such as "git diff*" also matches "git difftool", which runs any
    program it is given. The subcommand must be the second word of an allow
    pattern, so a longer name that only starts with it is blocked.

    Args:
        command: the Bash command line.
        allow_patterns: the Bash patterns of settings.json's allow list.
    """
    named = {
        pattern.split()[1].rstrip("*")
        for pattern in allow_patterns
        if pattern.startswith("git ") and len(pattern.split()) > 1
    }
    for segment in split_segments(command):
        words = command_words(segment)
        if len(words) >= 2 and words[0] == "git" and words[1] not in named:
            hook_lib.block(
                f"'git {words[1]}' is not a git command the allow list names.",
                f"Command: {command[:300]}",
            )


def _runs(command: str, subcommand: str) -> bool:
    return any(
        command_words(segment)[:2] == ["git", subcommand]
        for segment in split_segments(command)
    )


def _current_branch() -> str:
    branch = os.environ.get("MOCK_BRANCH")
    if branch is not None:
        return branch
    cwd = os.environ.get("HOOK_ORIG_CWD", ".")
    result = subprocess.run(
        ["git", "-C", cwd, "branch", "--show-current"],
        capture_output=True, text=True,
    )
    return result.stdout.strip()


def check_commit_on_main(command: str) -> None:
    """Block a git commit while the current branch is main.

    The branch is MOCK_BRANCH when that is set. Otherwise git reports it for
    the directory in HOOK_ORIG_CWD, or for the current directory.

    Args:
        command: the Bash command line.
    """
    if _runs(command, "commit") and _current_branch() == "main":
        hook_lib.block(
            "Cannot commit directly to main.",
            "Run: git checkout main && git pull && git checkout -b <type>/<description>",
            f"Command: {command[:300]}",
        )


def check_push_on_main(command: str) -> None:
    """Block a git push while the current branch is main.

    main changes only through a pull request that the user merges. The
    branch is found the way check_commit_on_main finds it.

    Args:
        command: the Bash command line.
    """
    if _runs(command, "push") and _current_branch() == "main":
        hook_lib.block(
            "Cannot push main.",
            "main changes only through a pull request that the user merges.",
            f"Command: {command[:300]}",
        )
