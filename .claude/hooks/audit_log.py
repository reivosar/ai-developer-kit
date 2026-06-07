#!/usr/bin/env python3
"""Appends structured tool invocation records to the audit log."""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_lib  # noqa: E402

_SECRET_KEY_RE = re.compile(r"secret|key|token|password|credential", re.IGNORECASE)


def _mask_secrets(tool_input: dict) -> dict:
    return {k: "***" if _SECRET_KEY_RE.search(k) else v for k, v in tool_input.items()}


def record(
    hook_event: str,
    tool_name: str,
    tool_input: dict,
    log_file: Optional[Path] = None,
) -> None:
    if log_file is None:
        log_file = hook_lib.REPO_ROOT / ".claude" / "audit.log"
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hook_event": hook_event,
        "tool_name": tool_name,
        "tool_input": _mask_secrets(tool_input),
    }
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with log_file.open("a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass
