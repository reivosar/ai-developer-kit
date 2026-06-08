#!/usr/bin/env python3
"""Detects path escapes and sensitive file access in commands and file paths."""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_lib  # noqa: E402

_SENSITIVE_RE = re.compile(
    r"~/\.ssh/"
    r"|~/\.aws/"
    r"|/(?:home|Users)/[^/]+/\.ssh/"
    r"|/(?:home|Users)/[^/]+/\.aws/"
    r"|/etc/passwd\b"
    r"|/etc/hosts\b"
    r"|/etc/shadow\b",
    re.IGNORECASE,
)

# Strip quoted strings so commit messages / -m args don't trigger false positives.
_QUOTED_RE = re.compile(r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'', re.DOTALL)


def check_sensitive_path(command: str) -> None:
    unquoted = _QUOTED_RE.sub("", command)
    if _SENSITIVE_RE.search(unquoted):
        hook_lib.block(
            "Command targets a sensitive system path.",
            f"Blocked pattern found in: {command[:200]}",
        )


def check_path_escape(path: str) -> None:
    if not path or os.environ.get("ANOMALY_PATH_ESCAPE_DISABLE"):
        return
    try:
        resolved = Path(path).resolve()
    except Exception:
        return
    try:
        resolved.relative_to(hook_lib.REPO_ROOT)
    except ValueError:
        hook_lib.block(
            f"File path escapes the repository root: {path}",
            f"All file operations must stay within {hook_lib.REPO_ROOT}",
        )
