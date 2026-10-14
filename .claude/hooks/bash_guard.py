#!/usr/bin/env python3
"""Bash command parsing, allow/deny enforcement, and python3 path guard."""
import fnmatch
import json
import os
import re
import shlex
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_lib  # noqa: E402


def _quote_state(char: str, in_single: bool, in_double: bool) -> tuple[bool, bool]:
    if char == "'" and not in_double:
        return not in_single, in_double
    if char == '"' and not in_single:
        return in_single, not in_double
    return in_single, in_double


def _separator_length(command: str, index: int) -> int:
    if command[index:index + 2] == "&&":
        return 2
    return 1 if command[index] in ";|" else 0


def _syntax_positions(command: str) -> list[tuple[int, bool, bool]]:
    positions: list[tuple[int, bool, bool]] = []
    in_single = in_double = False
    index = 0
    while index < len(command):
        if command[index] == "\\" and not in_single:
            index += 2  # the shell reads the character after a backslash as text
            continue
        in_single, in_double = _quote_state(command[index], in_single, in_double)
        positions.append((index, in_single, in_double))
        index += 1
    return positions


def split_segments(command: str) -> list[str]:
    """Split on &&, ;, and | outside of single or double quotes.

    A character after a backslash is text, as the shell reads it, so an
    escaped quote does not open or close a quoted part.
    """
    pieces: list[str] = []
    start = 0
    for index, in_single, in_double in _syntax_positions(command):
        skipped = in_single or in_double or index < start
        length = 0 if skipped else _separator_length(command, index)
        if length:
            pieces.append(command[start:index])
            start = index + length
    pieces.append(command[start:])
    segments = [piece.strip() for piece in pieces if piece.strip()]
    return segments if segments else [command]


def command_words(segment: str) -> list[str]:
    """Return the words of one command segment as the shell would split them.

    A segment with an unbalanced quote is split on whitespace instead.
    """
    try:
        return shlex.split(segment)
    except ValueError:
        return segment.split()


def load_patterns(settings_path: str, key: str) -> list[str]:
    """Return the Bash command patterns listed under permissions.<key>."""
    with open(settings_path) as f:
        settings = json.load(f)
    entries = settings.get("permissions", {}).get(key, [])
    return [e[5:-1] for e in entries if e.startswith("Bash(") and e.endswith(")")]


def is_denied(command: str, patterns: list[str]) -> bool:
    """Return True when the command or one of its segments matches a pattern."""
    candidates = [command] + split_segments(command)
    return any(fnmatch.fnmatch(c, p) for c in candidates for p in patterns)


def is_whitelisted(command: str, patterns: list[str]) -> bool:
    """Return True when every segment of the command matches a pattern."""
    segments = split_segments(command)
    return all(any(fnmatch.fnmatch(seg, p) for p in patterns) for seg in segments)


_SUBSTITUTION = "command substitution is not permitted. Run the inner command on its own."
_PROCESS_SUBSTITUTION = (
    "process substitution '<(' is not permitted. Run the inner command on its own."
)
_BACKGROUND = "background operator '&' is not permitted. Run each command separately."
_ANSI_C_QUOTING = (
    "ANSI-C quoting $'...' is not permitted: its escapes hide where a quote ends."
)
_UNQUOTED_OPERATORS = {
    ">": "shell redirect operator '>' is not permitted. "
         "Use explicit file-writing tools instead.",
    "|": "pipe operator '|' is not permitted. Run each command separately.",
    "\n": "a second command line is not permitted. Run each command separately.",
}
FIND_ACTIONS = (
    "-delete", "-exec", "-execdir", "-ok", "-okdir",
    "-fprint", "-fprint0", "-fprintf", "-fls",
)


def _is_lone_ampersand(command: str, index: int) -> bool:
    neighbors = command[max(index - 1, 0):index + 2]
    return command[index] == "&" and "&&" not in neighbors


def _operator_problem(command: str, index: int, in_double: bool) -> Optional[str]:
    char, pair = command[index], command[index:index + 2]
    if pair == "$(" or char == "`":
        return _SUBSTITUTION  # the shell runs it inside double quotes too
    if in_double:
        return None
    if pair == "$'":
        return _ANSI_C_QUOTING
    if pair == "<(":
        return _PROCESS_SUBSTITUTION
    if _is_lone_ampersand(command, index):
        return _BACKGROUND
    return _UNQUOTED_OPERATORS.get(char)


def check_raw_operators(command: str) -> None:
    """Block shell syntax that runs or chains a command the allow list never sees.

    Outside quotes: a redirect, a pipe, a lone '&', a second line, and
    process substitution. Outside single quotes: command substitution, which
    the shell also runs inside double quotes. A character after a backslash
    is text.
    """
    stripped = command.strip()
    for index, in_single, in_double in _syntax_positions(stripped):
        problem = None if in_single else _operator_problem(stripped, index, in_double)
        if problem:
            hook_lib.block(problem, f"Command: {command[:300]}")


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


def _runner_arguments(segment: str) -> list[str]:
    if not re.match(r'(python3|pytest)\s', segment):
        return []
    try:
        return shlex.split(segment)
    except ValueError:
        return []


def _first_script(arguments: list[str]) -> Optional[str]:
    scripts = [
        argument for argument in arguments[1:]
        if not argument.startswith('-') and argument.endswith('.py')
    ]
    return scripts[0] if scripts else None


def _script_path_problem(runner: str, script: str) -> Optional[str]:
    if script.startswith('/'):
        return (
            f"{runner}: absolute path '{script}' is not permitted. "
            "Use a relative path within the project."
        )
    if '../' in script:
        return f"{runner}: path traversal '{script}' is not permitted."
    if script.startswith(".claude/worktrees/"):
        return (
            f"{runner}: scripts under .claude/worktrees/ must be run "
            "from inside the worktree using a relative path."
        )
    return None


def check_python3_path(command: str) -> None:
    """Block python3 and pytest invocations referencing absolute paths, path
    traversal, or any script path under .claude/worktrees/."""
    for segment in split_segments(command):
        arguments = _runner_arguments(segment.strip())
        script = _first_script(arguments)
        problem = _script_path_problem(arguments[0], script) if script else None
        if problem:
            hook_lib.block(problem, f"Command: {command[:300]}")
