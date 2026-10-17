#!/usr/bin/env python3
"""Make an uncaught error in a hook block the tool call.

Claude Code blocks a tool call only when its hook exits with 2. Python ends
with 1 on an uncaught error, which lets the call through with every check
skipped. This module imports nothing but the standard library, so it can be
loaded before the modules that may fail.
"""
import os
import runpy
import sys
from pathlib import Path
from typing import Callable

BLOCKED = 2  # the exit status Claude Code reads as "do not run the tool"


def block_uncaught(
    error_type: type, error: BaseException, traceback: object,
    leave: Callable[[int], None] = os._exit,
) -> None:
    """Report an uncaught error as a block and end the process with 2.

    The signature is that of sys.excepthook.

    Args:
        error_type: the class of the uncaught error.
        error: the uncaught error.
        traceback: where it was raised; not printed.
        leave: ends the process with a status; a test passes its own.
    """
    print(f"BLOCKED: hook failed: {error_type.__name__}: {error}", file=sys.stderr)
    print(
        "  The action is blocked because the hook could not finish its checks.",
        file=sys.stderr,
    )
    sys.stderr.flush()
    leave(BLOCKED)


def install() -> None:
    """Block the tool call when the hook raises, even while it imports.

    Call this before importing any other hook module. A deliberate exit,
    such as sys.exit(0), is not an error and keeps its status.
    """
    sys.excepthook = block_uncaught


def run_entry_point(name: str, directory: Path = Path(__file__).resolve().parent) -> None:
    """Run a hook script in this directory as the main program.

    run-hook.py calls this after install(), so the script is compiled with
    the handler in place: a syntax error in the script itself blocks the
    tool call like any other error.

    Args:
        name: the script's file name, such as "pre-bash.py".
        directory: the directory that holds it; this module's by default.
    """
    runpy.run_path(str(directory / name), run_name="__main__")
