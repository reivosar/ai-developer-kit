#!/usr/bin/env python3
"""Notices: references to a changed function and duplicate definitions."""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from function_definitions import find_definitions  # noqa: E402
from tdd_guard import is_test_file  # noqa: E402

LISTED_LOCATIONS = 10
GIT_TIMEOUT = 10  # seconds; a hung search must not hold up every edit
_CONVENTIONAL_NAMES = {"main"}
_DEFINITION_KEYWORDS = "(def|func|function|fn|fun)"


def _is_noticed_file(file_path: str) -> bool:
    # Test files quote source code as fixture strings, which would be
    # read as definitions.
    if os.environ.get("REFERENCE_NOTICE_DISABLE"):
        return False
    return not is_test_file(file_path)


def _git(directory: str, *arguments: str) -> list[str]:
    command = ["git", "-C", directory, *arguments]
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=GIT_TIMEOUT
        )
    except (OSError, subprocess.SubprocessError):
        return []
    return result.stdout.splitlines() if result.returncode == 0 else []


def _existing_directory(file_path: str) -> str:
    directory = os.path.dirname(os.path.abspath(file_path))
    while not os.path.isdir(directory):
        directory = os.path.dirname(directory)
    return directory


def _path_in_repository(file_path: str) -> str:
    directory = _existing_directory(file_path)
    top_level = _git(directory, "rev-parse", "--show-toplevel")
    if not top_level:
        return ""
    repository_root = os.path.realpath(top_level[0])
    return os.path.relpath(os.path.realpath(file_path), repository_root)


def _grep_other_files(file_path: str, *grep_arguments: str) -> list[str]:
    own_path = _path_in_repository(file_path)
    lines = _git(
        _existing_directory(file_path), "grep", "-n", "--untracked",
        "--full-name", *grep_arguments, "--", ":/",
    )
    return [line for line in lines if line.split(":", 1)[0] != own_path]


def _reference_lines(file_path: str, name: str) -> list[str]:
    return _grep_other_files(file_path, "-w", "-F", "-e", name)


def _definition_lines(file_path: str, name: str) -> list[str]:
    pattern = f"{_DEFINITION_KEYWORDS}[[:space:]]+{name}[[:space:]]*[(<]"
    return _grep_other_files(file_path, "-E", "-e", pattern)


def _locations(lines: list[str]) -> str:
    shown = [":".join(line.split(":", 2)[:2])
             for line in lines[:LISTED_LOCATIONS]]
    hidden = len(lines) - len(shown)
    return ", ".join(shown) + (f" (+{hidden} more)" if hidden else "")


def _counted(count: int, noun: str) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


def _describe_references(name: str, lines: list[str]) -> str:
    file_count = len({line.split(":", 1)[0] for line in lines})
    return (
        f"`{name}` is referenced on {_counted(len(lines), 'line')} in"
        f" {_counted(file_count, 'other file')}: {_locations(lines)}."
        " Check each reference before finishing."
    )


def _describe_duplicate(name: str, lines: list[str]) -> str:
    return (
        f"`{name}` is already defined in {_locations(lines)}."
        " Reuse it instead of writing a second copy,"
        " or choose a distinct name."
    )


def _changed_names(definitions: dict, edited_definitions: dict) -> list[str]:
    return sorted(
        name for name, line in definitions.items()
        if edited_definitions.get(name) != line
    )


def _is_checked_for_duplicates(name: str) -> bool:
    return not name.startswith("_") and name not in _CONVENTIONAL_NAMES


def _added_names(definitions: dict, edited_definitions: dict) -> list[str]:
    return sorted(
        name for name in edited_definitions
        if name not in definitions and _is_checked_for_duplicates(name)
    )


def _notices(file_path: str, names: list[str], find_lines, describe) -> list:
    found = {name: find_lines(file_path, name) for name in names}
    return [describe(name, lines) for name, lines in found.items() if lines]


def for_edit(file_path: str, old_code: str, new_code: str) -> list[str]:
    """Return notices for an Edit: stale references and duplicate names."""
    if not _is_noticed_file(file_path):
        return []
    definitions = find_definitions(old_code, file_path)
    edited = find_definitions(new_code, file_path)
    changed = _changed_names(definitions, edited)
    added = _added_names(definitions, edited)
    return [
        *_notices(file_path, changed, _reference_lines, _describe_references),
        *_notices(file_path, added, _definition_lines, _describe_duplicate),
    ]


def for_write(file_path: str, content: str) -> list[str]:
    """Return notices for a Write: names already defined in another file."""
    return for_edit(file_path, "", content)
