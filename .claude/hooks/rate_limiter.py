#!/usr/bin/env python3
"""Session-scoped rate limiter for tool invocations."""
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_lib  # noqa: E402

STATE_FILE_VARIABLE = "RATE_STATE_FILE"
_WINDOW_SECONDS = 60
_LIMITS: dict[str, int] = {"bash": 30, "mcp": 10}


def _load_state(state_file: Path) -> dict:
    try:
        return json.loads(state_file.read_text())
    except Exception:
        return {}


def _save_state(state: dict, state_file: Path) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state))


def _default_state_file() -> Path:
    named = os.environ.get(STATE_FILE_VARIABLE)
    return Path(named) if named else hook_lib.REPO_ROOT / ".claude" / "rate-state.json"


def check_rate(
    session_id: str,
    tool_category: str,
    state_file: Optional[Path] = None,
) -> None:
    """Block a tool call once its session reaches the limit for its category.

    Calls are counted per session and tool category over the last
    _WINDOW_SECONDS seconds. Nothing is counted while RATE_LIMIT_DISABLE is
    set.

    Args:
        session_id: the Claude Code session the call belongs to.
        tool_category: the kind of call counted, such as "bash".
        state_file: where the counts are kept; when None, the file
            RATE_STATE_FILE names, or else .claude/rate-state.json.
    """
    if os.environ.get("RATE_LIMIT_DISABLE"):
        return
    if state_file is None:
        state_file = _default_state_file()
    now = time.time()
    cutoff = now - _WINDOW_SECONDS
    state = _load_state(state_file)
    session = state.setdefault(session_id, {})
    timestamps = [t for t in session.get(tool_category, []) if t > cutoff]
    limit = _LIMITS.get(tool_category, 30)
    if len(timestamps) >= limit:
        hook_lib.block(
            f"Rate limit exceeded: {tool_category} ({limit} calls / {_WINDOW_SECONDS}s).",
            "Wait before retrying or review the operation for runaway loops.",
        )
    timestamps.append(now)
    session[tool_category] = timestamps
    _save_state(state, state_file)
