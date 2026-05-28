#!/usr/bin/env python3
"""Guard MEMORY.md against exceeding the 200-line limit."""
import sys
from pathlib import Path

from hook_lib import block, read_stdin_json

LINE_LIMIT = 200
MEMORY_FILENAME = "memory/MEMORY.md"


def check_write(file_path: str, content: str) -> None:
    """Block a Write to MEMORY.md if content exceeds LINE_LIMIT lines."""
    if MEMORY_FILENAME not in file_path:
        return
    line_count = len(content.splitlines())
    if line_count > LINE_LIMIT:
        block(
            f"MEMORY.md would have {line_count} lines, exceeding the"
            f" {LINE_LIMIT}-line limit.",
            "Prune stale entries before adding new ones.",
        )


def check_edit(file_path: str) -> None:
    """Exit with error if MEMORY.md exceeds LINE_LIMIT lines after an Edit."""
    if MEMORY_FILENAME not in file_path:
        return
    path = Path(file_path)
    if not path.exists():
        return
    line_count = len(path.read_text().splitlines())
    if line_count > LINE_LIMIT:
        print(
            f"ERROR: MEMORY.md now has {line_count} lines, exceeding the"
            f" {LINE_LIMIT}-line limit. Prune stale entries.",
            file=sys.stderr,
        )
        sys.exit(1)


def main() -> None:
    data = read_stdin_json()
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if tool_name == "Write":
        check_write(file_path, tool_input.get("content", ""))
    elif tool_name == "Edit":
        check_edit(file_path)


if __name__ == "__main__":
    main()
