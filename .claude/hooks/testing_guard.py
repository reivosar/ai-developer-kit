#!/usr/bin/env python3
"""Guard: block tests that break the mechanically decidable test rules."""
import os
import re
import sys
from pathlib import Path
from typing import NamedTuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hook_lib import apply_edit, block, read_text  # noqa: E402
from tdd_guard import is_test_file  # noqa: E402

NAME_PATTERN = "test_<function>_<scenario>_<expected_outcome>"
_ALWAYS_TRUE = "assertion that is always true"
_SLEEP = "sleep in a test"
_SNAPSHOT = "snapshot test"


class _Language(NamedTuple):
    test_start: str  # regex with a group called "name"
    assertion: str
    forbidden: tuple  # (label, regex) pairs checked inside each test
    module_forbidden: tuple = ()  # (label, regex) pairs for the whole file
    min_name_words: int = 0


_PYTHON = _Language(
    test_start=r"^[ \t]*(?:async[ \t]+)?def[ \t]+(?P<name>test_\w+)[ \t]*\(",
    assertion=(
        r"^[ \t]*assert\b|\bpytest\.(?:raises|fail|warns)\b"
        r"|\w*assert\w*\(|\.fail\("
    ),
    forbidden=(
        (
            _ALWAYS_TRUE,
            r"^[ \t]*assert[ \t]+(?:True\b|(\d+)[ \t]*==[ \t]*\1\b)",
        ),
        (_SLEEP, r"^[ \t]*(?:await[ \t]+)?(?:time\.|asyncio\.)?sleep[ \t]*\("),
        (_SNAPSHOT, r"==[ \t]*snapshot\b|\bsnapshot\.assert_match\b"),
    ),
    module_forbidden=(
        ("__main__ runner block", r"""^if __name__ == ["']__main__["']"""),
        ("pass/fail counters", r"^[ \t]*global[ \t]+(?:passed|failed)\b"),
    ),
    min_name_words=3,
)
_JAVASCRIPT = _Language(
    test_start=r"""\b(?:it|test)\s*\(\s*(["'`])(?P<name>.*?)\1""",
    assertion=r"\bexpect\s*\(|\bassert\b|\.should\b",
    forbidden=(
        (
            _ALWAYS_TRUE,
            r"expect\(\s*true\s*\)\.toBe\(\s*true\s*\)"
            r"|\bassert(?:\.ok|\.isTrue)?\(\s*true\s*\)",
        ),
        (_SLEEP, r"\bsetTimeout\s*\(|\bsleep\s*\("),
        (_SNAPSHOT, r"\.toMatch(?:Inline)?Snapshot\s*\("),
    ),
)
_GO = _Language(
    test_start=r"^func[ \t]+(?P<name>Test\w+)[ \t]*\(",
    assertion=(
        r"\bt\.(?:Error|Errorf|Fatal|Fatalf|Fail|FailNow)\("
        r"|\b(?:assert|require)\.\w+\("
    ),
    forbidden=(
        (_ALWAYS_TRUE, r"\bassert\.True\(\s*t\s*,\s*true\s*\)"),
        (_SLEEP, r"\btime\.Sleep\s*\("),
    ),
)

_RUST = _Language(
    test_start=(
        r"#\[(?:\w+::)*test(?:\([^\]]*\))?\](?:\s*#\[[^\]]*\])*"
        r"\s*(?:pub\s+)?(?:async\s+)?fn\s+(?P<name>\w+)\s*\("
    ),
    assertion=r"\b\w*assert\w*!|\bpanic!|\bunreachable!|#\[should_panic",
    forbidden=(
        (
            _ALWAYS_TRUE,
            r"\bassert!\(\s*true\s*\)|\bassert_eq!\(\s*(\d+)\s*,\s*\1\s*\)",
        ),
        (_SLEEP, r"\bsleep\s*\("),
        (_SNAPSHOT, r"\bassert_\w*snapshot!|\binsta::"),
    ),
)

_LANGUAGES: dict[str, _Language] = {".py": _PYTHON, ".go": _GO, ".rs": _RUST}
# Rust keeps unit tests in the source file, so every Rust file is read; code
# outside a test function is never part of a test block.
_INLINE_TEST_EXTENSIONS = {".rs"}
for _extension in (".js", ".jsx", ".ts", ".tsx", ".mjs", ".mts"):
    _LANGUAGES[_extension] = _JAVASCRIPT


def _test_blocks(code: str, language: _Language) -> list[tuple[str, str]]:
    starts = list(re.finditer(language.test_start, code, re.MULTILINE))
    ends = [start.start() for start in starts[1:]] + [len(code)]
    return [
        (start.group("name"), code[start.start():end])
        for start, end in zip(starts, ends)
    ]


def _has_enough_words(name: str, language: _Language) -> bool:
    words = [word for word in name.split("_")[1:] if word]
    return len(words) >= language.min_name_words


def _test_violations(name: str, body: str, language: _Language) -> set[str]:
    found = {
        label for label, pattern in language.forbidden
        if re.search(pattern, body, re.MULTILINE)
    }
    if not re.search(language.assertion, body, re.MULTILINE):
        found.add("no assertion")
    if not _has_enough_words(name, language):
        found.add(f"name needs {NAME_PATTERN}")
    return {f"{name}: {label}" for label in found}


def _module_violations(code: str, language: _Language) -> set[str]:
    return {
        f"module: {label}" for label, pattern in language.module_forbidden
        if re.search(pattern, code, re.MULTILINE)
    }


def find_violations(code: str, file_path: str) -> set[str]:
    """Return the test-rule violations found in a test file's text."""
    _, extension = os.path.splitext(file_path)
    language = _LANGUAGES.get(extension.lower())
    if language is None:
        return set()
    violations = _module_violations(code, language)
    for name, body in _test_blocks(code, language):
        violations |= _test_violations(name, body, language)
    return violations


def _is_guarded_file(file_path: str) -> bool:
    if os.environ.get("TESTING_GUARD_DISABLE"):
        return False
    extension = os.path.splitext(file_path)[1].lower()
    return is_test_file(file_path) or extension in _INLINE_TEST_EXTENSIONS


def _block_added(file_path: str, added: set[str]) -> None:
    block(
        f"'{os.path.basename(file_path)}' adds a test that breaks the"
        " test rules.",
        *sorted(added),
        "See .claude/docs/testing.md.",
    )


def check_write(file_path: str, content: str) -> None:
    """Block a Write that creates a test file with a violation."""
    if not _is_guarded_file(file_path):
        return
    violations = find_violations(content, file_path)
    if violations:
        _block_added(file_path, violations)


def check_edit(
    file_path: str, old_string: str, new_string: str, replace_all: bool = False
) -> None:
    """Block an Edit that adds a violation to a test file.

    Violations already in the file are not counted, so a legacy test file
    can still be edited and cleaned up in steps.
    """
    if not _is_guarded_file(file_path) or not Path(file_path).is_file():
        return
    current_text = read_text(file_path)
    edited_text = apply_edit(current_text, old_string, new_string, replace_all)
    existing = find_violations(current_text, file_path)
    added = find_violations(edited_text, file_path) - existing
    if added:
        _block_added(file_path, added)
