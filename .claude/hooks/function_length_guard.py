#!/usr/bin/env python3
"""Guard: block a function whose body is longer than the limit."""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from function_lengths import function_lengths  # noqa: E402
from hook_lib import apply_edit, block, read_text  # noqa: E402
from tdd_guard import is_test_file  # noqa: E402

LIMIT = 20  # body lines; blank lines, comments, and the docstring are not counted


def _over_limit(lengths: list[tuple[str, int]], accepted: dict[str, int]) -> list[str]:
    return [
        f"{name}: body is {length} lines; the limit is {LIMIT}"
        for name, length in lengths
        if length > max(LIMIT, accepted.get(name, 0))
    ]


def find_violations(code: str, file_path: str) -> list[str]:
    """Return a message for each function whose body is over the limit."""
    return _over_limit(function_lengths(code, file_path), {})


def _is_guarded_file(file_path: str) -> bool:
    if os.environ.get("FUNCTION_LENGTH_GUARD_DISABLE"):
        return False
    return not is_test_file(file_path)


def _block_added(file_path: str, added: list[str]) -> None:
    block(
        f"'{os.path.basename(file_path)}' adds a function body longer than"
        f" {LIMIT} lines.",
        *added,
        "Extract until each function fits."
        " See 'Universal Rules' in .claude/docs/code-style.md.",
    )


def check_write(file_path: str, content: str) -> None:
    """Block a Write that creates a source file with an over-limit function."""
    if not _is_guarded_file(file_path):
        return
    violations = find_violations(content, file_path)
    if violations:
        _block_added(file_path, violations)


def _longest_by_name(lengths: list[tuple[str, int]]) -> dict[str, int]:
    longest: dict[str, int] = {}
    for name, length in lengths:
        longest[name] = max(length, longest.get(name, 0))
    return longest


def check_edit(
    file_path: str, old_string: str, new_string: str, replace_all: bool = False
) -> None:
    """Block an Edit that adds or lengthens an over-limit function.

    A function that is already over the limit may be edited as long as its
    body does not grow, so existing code can be shortened in steps.

    Args:
        file_path: the file the Edit changes.
        old_string: the text the Edit replaces.
        new_string: the text it puts in its place.
        replace_all: whether every occurrence of old_string is replaced.
    """
    if not _is_guarded_file(file_path) or not Path(file_path).is_file():
        return
    current_text = read_text(file_path)
    edited_text = apply_edit(current_text, old_string, new_string, replace_all)
    accepted = _longest_by_name(function_lengths(current_text, file_path))
    added = _over_limit(function_lengths(edited_text, file_path), accepted)
    if added:
        _block_added(file_path, added)
