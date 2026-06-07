#!/usr/bin/env python3
"""PostToolUse audit logging entry point."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audit_log  # noqa: E402
from hook_lib import read_stdin_json  # noqa: E402


def main() -> None:
    data = read_stdin_json()
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    audit_log.record("PostToolUse", tool_name, tool_input)
    sys.exit(0)


if __name__ == "__main__":
    main()
