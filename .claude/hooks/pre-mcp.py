#!/usr/bin/env python3
"""PreToolUse[mcp__.*] entry point."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audit_log  # noqa: E402
import mcp_guard  # noqa: E402
import rate_limiter  # noqa: E402
from hook_lib import read_stdin_json  # noqa: E402


def main() -> None:
    data = read_stdin_json()
    tool_name = data.get("tool_name", "")
    session_id = data.get("session_id", "unknown")
    tool_input = data.get("tool_input", {})
    audit_log.record("PreToolUse", tool_name, tool_input)
    mcp_guard.check_mcp_tool(tool_name)
    rate_limiter.check_rate(session_id, "mcp")
    sys.exit(0)


if __name__ == "__main__":
    main()
