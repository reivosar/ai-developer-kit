#!/usr/bin/env python3
"""Guard: block names assembled from strings at runtime."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hook_lib import block  # noqa: E402
from tdd_guard import is_test_file  # noqa: E402

# A "part" is the start of an expression that builds a string at runtime.
_PY_PART = (
    r"""(?:[fF][rR]?["']"""
    r"""|["'][^"'\n]*["']\s*(?:\+|%|\.format\()"""
    r"""|[\w.]+\s*\+)"""
)
_JS_STRING_PART = r"""(?:`[^`\n]*\$\{|["'][^"'\n]*["']\s*\+)"""
_JS_PART = rf"(?:{_JS_STRING_PART}|[\w.$]+\s*\+)"
_RB_PART = r"""(?:["'][^"'\n]*#\{|["'][^"'\n]*["']\s*\+)"""
_CONCAT_PART = r"""(?:"[^"\n]*"\s*\+|[\w.]+\s*\+)"""

_PYTHON = [
    rf"\b(?:get|set|has|del)attr\s*\([^,()\n]+,\s*{_PY_PART}",
    rf"\b(?:import_module|__import__)\s*\(\s*{_PY_PART}",
    rf"\b(?:globals|locals)\(\)\s*\[\s*{_PY_PART}",
]
_JAVASCRIPT = [
    rf"\b(?:require|import)\s*\(\s*{_JS_PART}",
    rf"\[\s*{_JS_STRING_PART}[^\]\n]*\]\s*\(",
]
_RUBY = [
    rf"\b(?:public_send|send|const_get|define_method)\s*\(?\s*{_RB_PART}",
]
_JVM = [
    rf"\b(?:Class\.forName|getMethod|getDeclaredMethod)\s*\(\s*{_CONCAT_PART}",
]
_GO = [rf"\bMethodByName\s*\(\s*{_CONCAT_PART}"]

_PATTERNS_BY_EXTENSION: dict[str, list[str]] = {
    ".py": _PYTHON,
    ".rb": _RUBY,
    ".java": _JVM,
    ".kt": _JVM,
    ".go": _GO,
}
for _extension in (".js", ".jsx", ".ts", ".tsx", ".mjs", ".mts"):
    _PATTERNS_BY_EXTENSION[_extension] = _JAVASCRIPT


def _is_guarded_file(file_path: str) -> bool:
    if os.environ.get("DYNAMIC_NAME_GUARD_DISABLE"):
        return False
    return not is_test_file(file_path)


def _count_assembled_names(code: str, file_path: str) -> int:
    _, extension = os.path.splitext(file_path)
    patterns = _PATTERNS_BY_EXTENSION.get(extension.lower(), [])
    return sum(len(re.findall(pattern, code)) for pattern in patterns)


def check(file_path: str, old_code: str, new_code: str) -> None:
    """Block a change that adds a name assembled from strings at runtime.

    Occurrences already present in old_code are not counted, so code next
    to an existing dynamic lookup can still be edited.
    """
    if not _is_guarded_file(file_path):
        return
    existing = _count_assembled_names(old_code, file_path)
    if _count_assembled_names(new_code, file_path) > existing:
        block(
            f"'{os.path.basename(file_path)}' adds a name assembled at"
            " runtime.",
            "Refer to the function, module, or key by its full literal name"
            " so a text search finds it.",
        )
