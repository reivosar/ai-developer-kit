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


def read_text(file_path: str) -> str:
    """Return a file's text; undecodable bytes are replaced, not raised."""
    return Path(file_path).read_text(errors="replace")


def apply_edit(
    text: str, old_string: str, new_string: str, replace_all: bool
) -> str:
    """Return text as the Edit tool would leave it."""
    replacement_count = -1 if replace_all else 1
    return text.replace(old_string, new_string, replacement_count)


def read_stdin_json() -> dict:
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def emit_additional_context(hook_event: str, notices: list[str]) -> None:
    """Print notices as non-blocking context that the agent reads."""
    if not notices:
        return
    context = {
        "hookEventName": hook_event,
        "additionalContext": "\n".join(notices),
    }
    print(json.dumps({"hookSpecificOutput": context}))


def block(reason: str, *detail_lines: str) -> NoReturn:
    print(f"BLOCKED: {reason}", file=sys.stderr)
    for line in detail_lines:
        print(f"  {line}", file=sys.stderr)
    sys.exit(2)
