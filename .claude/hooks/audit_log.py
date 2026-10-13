#!/usr/bin/env python3
"""Appends structured tool invocation records to the session's audit file."""
import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_lib  # noqa: E402

AUDIT_RECORD = "audit.jsonl"
_SECRET_KEY_RE = re.compile(r"secret|key|token|password|credential", re.IGNORECASE)


def _mask_secrets(tool_input: dict) -> dict:
    return {k: "***" if _SECRET_KEY_RE.search(k) else v for k, v in tool_input.items()}


def record(hook_event: str, tool_name: str, tool_input: dict) -> None:
    """Append one tool call, with its secrets masked, to the session's audit file.

    The file is audit.jsonl in the session's directory under .claude/logs. A
    record that cannot be written is dropped, so auditing never blocks a call.
    """
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hook_event": hook_event,
        "tool_name": tool_name,
        "tool_input": _mask_secrets(tool_input),
    }
    hook_lib.append_record(AUDIT_RECORD, entry)
