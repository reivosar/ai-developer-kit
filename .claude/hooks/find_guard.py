#!/usr/bin/env python3
"""Guard: find may list files; it may not delete, run commands, or write."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_lib  # noqa: E402
from bash_guard import command_words, split_segments  # noqa: E402

FIND_ACTIONS = (
    "-delete", "-exec", "-execdir", "-ok", "-okdir",
    "-fprint", "-fprint0", "-fprintf", "-fls",
)


def check_find_actions(command: str) -> None:
    """Block a find that deletes, runs a command, or writes a file.

    find is allowed for listing files; the actions in FIND_ACTIONS do more.
    """
    for segment in split_segments(command):
        words = command_words(segment)
        actions = [word for word in words if word in FIND_ACTIONS]
        if words[:1] == ["find"] and actions:
            hook_lib.block(
                f"'find {actions[0]}' is not permitted: find may list files,"
                " not act on them.",
                f"Command: {command[:300]}",
            )
