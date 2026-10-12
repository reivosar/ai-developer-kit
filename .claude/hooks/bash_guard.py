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


def split_segments(command: str) -> list[str]:
    """Split on &&, ;, and | outside of single or double quotes."""
    pieces: list[str] = []
    in_single = in_double = False
    start = index = 0
    while index < len(command):
        in_single, in_double = _quote_state(command[index], in_single, in_double)
        quoted = in_single or in_double
        length = 0 if quoted else _separator_length(command, index)
        if length:
            pieces.append(command[start:index])
            start = index + length
        index += length or 1
    pieces.append(command[start:])
    segments = [piece.strip() for piece in pieces if piece.strip()]
    return segments if segments else [command]


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


def check_raw_operators(command: str) -> None:
    """Block '>' or '|' outside of quotes before the allow list runs."""
    in_single = in_double = False
    for ch in command:
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif not in_single and not in_double:
            if ch == '>':
                hook_lib.block(
                    "shell redirect operator '>' is not permitted. "
                    "Use explicit file-writing tools instead.",
                    f"Command: {command[:300]}",
                )
            elif ch == '|':
                hook_lib.block(
                    "pipe operator '|' is not permitted. "
                    "Run each command separately.",
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
