#!/usr/bin/env python3
"""
Pre-tool-call hook for the Write tool.
Blocks Write when the target file already exists — use Edit instead.
"""
import sys
import json
import os

try:
    data = json.load(sys.stdin)
    file_path = data.get("tool_input", {}).get("file_path", "")
except Exception:
    sys.exit(0)

if not file_path:
    sys.exit(0)

if os.path.exists(file_path):
    print(
        f"BLOCKED: '{file_path}' already exists. Use Edit to modify existing files.",
        file=sys.stderr,
    )
    sys.exit(2)

sys.exit(0)
