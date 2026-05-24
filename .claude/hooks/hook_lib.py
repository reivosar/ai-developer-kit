"""Shared hook utilities for Python hooks."""
import json
import subprocess
import sys
from pathlib import Path
from typing import NoReturn


def _find_repo_root() -> Path:
    hooks_dir = Path(__file__).resolve().parent
    git_common = subprocess.check_output(
        ["git", "-C", str(hooks_dir), "rev-parse", "--git-common-dir"],
        text=True,
    ).strip()
    p = Path(git_common)
    if p.is_absolute():
        return p.parent
    toplevel = subprocess.check_output(
        ["git", "-C", str(hooks_dir), "rev-parse", "--show-toplevel"],
        text=True,
    ).strip()
    return Path(toplevel).resolve()


REPO_ROOT: Path = _find_repo_root()
WORKTREES_DIR: Path = REPO_ROOT / ".claude" / "worktrees"


def read_stdin_json() -> dict:
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def block(reason: str, *detail_lines: str) -> NoReturn:
    print(f"BLOCKED: {reason}", file=sys.stderr)
    for line in detail_lines:
        print(f"  {line}", file=sys.stderr)
    sys.exit(2)
