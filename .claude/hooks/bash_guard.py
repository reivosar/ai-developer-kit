#!/usr/bin/env python3
"""Bash command parsing, allow/deny enforcement, and python3 path guard."""
import fnmatch
import json
import os
import re
import shlex
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_lib  # noqa: E402


def split_segments(command: str) -> list[str]:
    """Split on &&, ;, and | outside of single or double quotes."""
    segments: list[str] = []
    current: list[str] = []
    in_single = in_double = False
    i = 0
    while i < len(command):
        c = command[i]
        if c == "'" and not in_double:
            in_single = not in_single
            current.append(c)
        elif c == '"' and not in_single:
            in_double = not in_double
            current.append(c)
        elif not in_single and not in_double:
            if command[i:i + 2] == "&&":
                seg = "".join(current).strip()
                if seg:
                    segments.append(seg)
                current = []
                i += 2
                continue
            elif c in (";", "|"):
                seg = "".join(current).strip()
                if seg:
                    segments.append(seg)
                current = []
                i += 1
                continue
            else:
                current.append(c)
        else:
            current.append(c)
        i += 1
    seg = "".join(current).strip()
    if seg:
        segments.append(seg)
    return segments if segments else [command]


def load_patterns(settings_path: str, key: str) -> list[str]:
    with open(settings_path) as f:
        settings = json.load(f)
    entries = settings.get("permissions", {}).get(key, [])
    return [e[5:-1] for e in entries if e.startswith("Bash(") and e.endswith(")")]


def is_denied(command: str, patterns: list[str]) -> bool:
    candidates = [command] + split_segments(command)
    return any(fnmatch.fnmatch(c, p) for c in candidates for p in patterns)


def is_whitelisted(command: str, patterns: list[str]) -> bool:
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


def check_python3_path(command: str) -> None:
    """Block python3 invocations referencing absolute paths or path traversal."""
    for seg in split_segments(command):
        seg = seg.strip()
        if not re.match(r'python3\s', seg):
            continue
        try:
            args = shlex.split(seg)
        except ValueError:
            continue
        for arg in args[1:]:
            if arg.startswith('-'):
                continue
            if arg.endswith('.py'):
                if arg.startswith('/'):
                    hook_lib.block(
                        f"python3: absolute path '{arg}' is not permitted. "
                        "Use a relative path within the project.",
                        f"Command: {command[:300]}",
                    )
                if '../' in arg:
                    hook_lib.block(
                        f"python3: path traversal '{arg}' is not permitted.",
                        f"Command: {command[:300]}",
                    )
                break
