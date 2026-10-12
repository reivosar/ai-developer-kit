#!/usr/bin/env python3
"""Guard: block a commit whose staged files fail static analysis."""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from commit_guard import is_commit, staged_files  # noqa: E402
from hook_lib import block  # noqa: E402

SCRIPT = Path(__file__).with_name("static-analysis.sh")
TIMEOUT = 300  # seconds
OUTPUT_LINES = 30


def _run_analysis() -> subprocess.CompletedProcess:
    environment = {**os.environ, "STATIC_ANALYSIS_MODE": "staged"}
    return subprocess.run(
        [str(SCRIPT)], capture_output=True, text=True, timeout=TIMEOUT,
        env=environment,
    )


def _block_findings(result: subprocess.CompletedProcess) -> None:
    findings = (result.stdout + result.stderr).strip().splitlines()
    block(
        "Static analysis found problems in the staged files.",
        *findings[-OUTPUT_LINES:],
        "Fix them, stage the fixes, and commit again.",
    )


def check_staged_files(command: str) -> None:
    """Block a git commit whose staged files fail static analysis.

    static-analysis.sh lints the staged files. Any other command, a commit
    with nothing staged, and every commit while STATIC_ANALYSIS_GUARD_DISABLE
    is set are let through. A script that cannot run blocks the commit.
    """
    if os.environ.get("STATIC_ANALYSIS_GUARD_DISABLE") or not is_commit(command):
        return
    if not staged_files():
        return
    try:
        result = _run_analysis()
    except (OSError, subprocess.SubprocessError) as error:
        block("Static analysis could not run.", str(error))
    if result.returncode != 0:
        _block_findings(result)
