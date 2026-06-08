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


def check_rate(
    session_id: str,
    tool_category: str,
    state_file: Optional[Path] = None,
) -> None:
    if os.environ.get("RATE_LIMIT_DISABLE"):
        return
    if state_file is None:
        state_file = hook_lib.REPO_ROOT / ".claude" / "rate-state.json"
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
