#!/usr/bin/env python3
"""Guard: block public code whose doc comment is missing or does not fit it."""


import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from doc_comments import Definition, find_public_definitions  # noqa: E402
from hook_lib import apply_edit, block, read_text  # noqa: E402
from tdd_guard import is_test_file  # noqa: E402

_COMMENT_MARKERS = re.compile(r"[/*\s]")
_TAGGED_PARAMETER = re.compile(
    r"@param\s+(?:\{[^}]*\}\s*)?\[?(?P<name>[A-Za-z_$][\w$]*)"
)
_ARGS_SECTION = re.compile(
    r"^(?:Args|Arguments|Parameters):[ \t]*\n(?P<body>(?:[ \t]+.*\n?|[ \t]*\n)*)",
    re.MULTILINE,
)
_ARGS_ENTRY = re.compile(
    r"^(?P<indent>[ \t]+)\*{0,2}(?P<name>\w+)[ \t]*(?:\([^)]*\))?:"
)
_GO_ARTICLE = r"(?:(?:A|An|The)\s+)?"


def _google_parameters(doc: str) -> Optional[set]:
    section = _ARGS_SECTION.search(doc)
    if section is None:
        return None
    lines = section.group("body").splitlines()
    entries = [entry for entry in map(_ARGS_ENTRY.match, lines) if entry]
    # A continuation line is indented deeper than the entry it continues.
    indent = min((len(entry.group("indent")) for entry in entries), default=0)
    return {
        entry.group("name") for entry in entries
        if len(entry.group("indent")) == indent
    }


def _tagged_parameters(doc: str) -> Optional[set]:
    names = {found.group("name") for found in _TAGGED_PARAMETER.finditer(doc)}
    return names or None


def _documented_parameters(doc: str, extension: str) -> Optional[set]:
    if extension == ".py":
        return _google_parameters(doc)
    return _tagged_parameters(doc)


def _parameter_violations(definition: Definition, documented: set) -> list[str]:
    name, params = definition.name, definition.params
    removed = [
        f"{name}: doc comment names parameter '{parameter}',"
        " which the signature does not have"
        for parameter in sorted(documented - set(params))
    ]
    omitted = [
        f"{name}: doc comment lists parameters but omits '{parameter}'"
        for parameter in params if parameter not in documented
    ]
    return removed + omitted


def _starts_with_name(doc: str, name: str) -> bool:
    return re.match(_GO_ARTICLE + re.escape(name) + r"\b", doc) is not None


def _definition_violations(definition: Definition, extension: str) -> list[str]:
    name, doc = definition.name, definition.doc or ""
    if not _COMMENT_MARKERS.sub("", doc):
        return [f"{name}: no doc comment"]
    if extension == ".go" and not _starts_with_name(doc, name):
        return [f"{name}: doc comment must start with '{name}'"]
    documented = _documented_parameters(doc, extension)
    if documented is None or definition.params is None:
        return []
    return _parameter_violations(definition, documented)


def find_violations(code: str, file_path: str) -> list[str]:
    """Return the doc comment violations in a source file's text.

    A public function, method, or type needs a doc comment. A Go comment
    must start with the name it documents. A comment that lists parameters,
    through an Args section in Python or @param tags elsewhere, must list
    exactly the parameters the signature has.
    """
    extension = os.path.splitext(file_path)[1].lower()
    return [
        violation
        for definition in find_public_definitions(code, file_path)
        for violation in _definition_violations(definition, extension)
    ]


def _is_guarded_file(file_path: str) -> bool:
    if os.environ.get("DOC_COMMENT_GUARD_DISABLE"):
        return False
    return not is_test_file(file_path)


def _block_added(file_path: str, added: list[str]) -> None:
    block(
        f"'{os.path.basename(file_path)}' adds public code whose doc comment"
        " is missing or does not fit it.",
        *added,
        "See 'Doc Comments' in .claude/docs/code-style.md.",
    )


def check_write(file_path: str, content: str) -> None:
    """Block a Write that creates a source file with a violation."""
    if not _is_guarded_file(file_path):
        return
    violations = find_violations(content, file_path)
    if violations:
        _block_added(file_path, violations)


def check_edit(
    file_path: str, old_string: str, new_string: str, replace_all: bool = False
) -> None:
    """Block an Edit that adds a violation to a source file.

    Violations already in the file are not counted, so existing code can
    still be edited and documented in steps.
    """
    if not _is_guarded_file(file_path) or not Path(file_path).is_file():
        return
    current_text = read_text(file_path)
    edited_text = apply_edit(current_text, old_string, new_string, replace_all)
    existing = Counter(find_violations(current_text, file_path))
    added = Counter(find_violations(edited_text, file_path)) - existing
    if added:
        _block_added(file_path, sorted(added))
