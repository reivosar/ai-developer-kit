#!/usr/bin/env python3
"""Guard: block git options that force, delete, discard, or overwrite."""
import os
import re
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

    Args:
        command: the Bash command line.
    """
    for segment in split_segments(command):
        words = command_words(segment)
        if len(words) >= 2 and words[0] == "git":
            _block_forbidden_use(words, command)
            _block_staging_everything(words, command)
