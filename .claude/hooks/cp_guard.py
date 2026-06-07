#!/usr/bin/env python3
"""cp operation safety guards."""
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Generator

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_lib  # noqa: E402
from bash_guard import split_segments  # noqa: E402

_BLOCKED_OPTIONS = {'-t', '--target-directory', '-f', '--force'}


def _parse_cp_segments(command: str) -> Generator[list[str], None, None]:
    """Yield parsed arg lists for each cp segment in command."""
    for seg in split_segments(command):
        seg = seg.strip()
        if not re.match(r'cp\s', seg):
            continue
        try:
            yield shlex.split(seg)
        except ValueError:
            continue


def check_cp_destination(command: str) -> None:
    """Move an existing cp destination to trash before copying."""
    for args in _parse_cp_segments(command):
        positional = [a for a in args[1:] if not a.startswith('-')]
        if len(positional) < 2:
            continue
        dst = positional[-1].rstrip('/')
        if not dst or dst in ('.', '..'):
            continue
        dst_path = os.path.expanduser(dst)
        if not os.path.exists(dst_path):
            continue
        trash_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trash.sh')
        result = subprocess.run(['bash', trash_script, dst_path], capture_output=True)
        if result.returncode != 0:
            hook_lib.block(
                f"could not trash existing destination '{dst_path}' before copy — "
                f"{result.stderr.decode().strip()}",
                f"Command: {command[:300]}",
            )
        print(f"INFO: moved existing '{dst_path}' to trash before copy", file=sys.stderr)


def check_cp_options(command: str) -> None:
    """Block cp invocations with force or target-directory options."""
    for args in _parse_cp_segments(command):
        for arg in args[1:]:
            if arg in _BLOCKED_OPTIONS or arg.startswith('--target-directory='):
                hook_lib.block(
                    f"cp option '{arg}' is not permitted.",
                    f"Command: {command[:300]}",
                )


def check_cp_source(command: str) -> None:
    """Block cp invocations whose source is outside the project root."""
    for args in _parse_cp_segments(command):
        positional = [a for a in args[1:] if not a.startswith('-')]
        if len(positional) < 2:
            continue
        for src in positional[:-1]:
            try:
                Path(src).resolve().relative_to(hook_lib.REPO_ROOT)
            except ValueError:
                hook_lib.block(
                    f"cp source '{src}' is outside the project root and is not permitted.",
                    f"Command: {command[:300]}",
                )
