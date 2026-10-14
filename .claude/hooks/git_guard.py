#!/usr/bin/env python3
"""Git operation safety guards."""
import os
import re
import subprocess
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_lib  # noqa: E402
from bash_guard import command_words, split_segments  # noqa: E402

# Per git subcommand: the letters of the short options, and the long options,
# that force, delete, or discard. A letter counts wherever it sits in a
# cluster such as -qf.
_FORBIDDEN_OPTIONS: dict[str, tuple[str, tuple[str, ...]]] = {
    "switch": ("fCd", ("--discard-changes", "--detach")),
    "checkout": ("fB", ()),
    "branch": ("DfMmCcu", ("--move", "--copy", "--set-upstream-to", "--unset-upstream")),
    "tag": ("df", ("--delete",)),
    "fetch": ("f", ("--upload-pack",)),
    "worktree": ("fB", ()),
    "add": ("fu", ("--update",)),
    "commit": ("an", ("--amend", "--no-verify", "--all")),
    "grep": ("O", ("--open-files-in-pager",)),
}
# For every subcommand: --force and its variants, and --output, which writes
# a file over whatever is there.
_FORCE_PREFIX = "--force"
_OUTPUT_OPTION = "--output"
_SHORT_CLUSTER_RE = re.compile(r"^-[A-Za-z]+$")
# Pathspecs that name every file, so git add would stage changes the task
# did not make.
_EVERY_FILE = (".", "./", ":/", "*")


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


def _forbidden_option(words: list[str]) -> Optional[str]:
    letters, long_options = _FORBIDDEN_OPTIONS.get(words[1], ("", ()))
    for word in words[2:]:
        name = word.partition("=")[0]
        if name == _OUTPUT_OPTION or name.startswith(_FORCE_PREFIX):
            return word
        if name in long_options:
            return word
        if _SHORT_CLUSTER_RE.match(word) and set(word[1:]) & set(letters):
            return word
    return None


def _fetch_into_local_branch(words: list[str]) -> Optional[str]:
    if words[1] != "fetch":
        return None
    refspecs = [
        word for word in words[2:]
        if not word.startswith("-") and (":" in word or word.startswith("+"))
    ]
    return refspecs[0] if refspecs else None


def _block_forbidden_use(words: list[str], command: str) -> None:
    option = _forbidden_option(words)
    if option:
        hook_lib.block(
            f"'{option}' is not permitted with git {words[1]}:"
            " it forces, deletes, discards, or overwrites.",
            "Ask the user to run it.",
            f"Command: {command[:300]}",
        )
    refspec = _fetch_into_local_branch(words)
    if refspec:
        hook_lib.block(
            f"git fetch '{refspec}' writes to a local branch and is not permitted.",
            "Fetch the remote branch alone: git fetch origin <branch>.",
            f"Command: {command[:300]}",
        )


def _block_staging_everything(words: list[str], command: str) -> None:
    pathspecs = [word for word in words[2:] if word in _EVERY_FILE]
    if words[1] == "add" and pathspecs:
        hook_lib.block(
            f"'git add {pathspecs[0]}' stages every change, not only the task's.",
            "Stage the files the task changed by name.",
            f"Command: {command[:300]}",
        )


def check_forbidden_options(command: str) -> None:
    """Block a git command whose option forces, deletes, discards, or overwrites.

    The options are listed per subcommand in _FORBIDDEN_OPTIONS. --force and
    --output are blocked for every subcommand, and so is a git fetch that
    names a local branch to write to. A git add of every file is blocked too.
    """
    for segment in split_segments(command):
        words = command_words(segment)
        if len(words) >= 2 and words[0] == "git":
            _block_forbidden_use(words, command)
            _block_staging_everything(words, command)


def check_git_subcommand(command: str, allow_patterns: list[str]) -> None:
    """Block a git subcommand that the allow list does not name.

    A pattern such as "git diff*" also matches "git difftool", which runs any
    program it is given. The subcommand must be the second word of an allow
    pattern, so a longer name that only starts with it is blocked.
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
    """
    if _runs(command, "push") and _current_branch() == "main":
        hook_lib.block(
            "Cannot push main.",
            "main changes only through a pull request that the user merges.",
            f"Command: {command[:300]}",
        )
