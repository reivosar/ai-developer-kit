#!/usr/bin/env python3
"""Guard: block a function whose body is longer than the limit."""
import ast
import os
import re
import sys
from pathlib import Path
from typing import Iterator, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hook_lib import apply_edit, block, read_text  # noqa: E402
from tdd_guard import is_test_file  # noqa: E402

LIMIT = 20  # body lines; blank lines, comments, and the docstring are not counted
_PYTHON_FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)
# Comments and string literals, which may hold braces that open no block.
_LITERALS = re.compile(
    r"""//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*'|`(?:\\.|[^`\\])*`""",
    re.DOTALL,
)
# What may stand between a parameter list and the brace that opens the body.
_BODY_OPENING = re.compile(r"[^;={}]*?(?:=>[^;={}]*?)?\{")
# A name followed by "(...) {" that is a statement or a call, not a definition.
_NOT_DEFINITIONS = {
    "if", "for", "while", "switch", "catch", "try", "when", "with", "do",
    "else", "return", "new", "throw", "await", "yield", "case", "assert",
    "function", "synchronized", "super",
}
_GO = (r"^[ \t]*func[ \t]+(?:\([^)\n]*\)[ \t]*)?(?P<name>\w+)[ \t]*(?:\[[^\]\n]*\])?\(",)
_KOTLIN = (
    r"^[ \t]*(?:[\w@]+[ \t]+)*?fun[ \t]+(?:<[^>\n]+>[ \t]+)?(?:[\w<>?,.]+\.)?"
    r"(?P<name>\w+)[ \t]*\(",
)
# A method: indented, optional modifiers and types, then the name.
_MEMBER = (
    r"^[ \t]+(?P<prefix>(?:[\w<>\[\],.?@$]+[ \t]+)*?)(?P<name>[\w$#]+)[ \t]*"
    r"(?:<[^>\n]*>)?[ \t]*\("
)
_JAVASCRIPT = (
    r"\bfunction\*?[ \t]+(?P<name>[\w$]+)[ \t]*(?:<[^>\n]*>)?[ \t]*\(",
    r"\b(?:const|let|var)[ \t]+(?P<name>[\w$]+)[ \t]*(?::[^=\n]+)?=[ \t]*"
    r"(?:async[ \t]*)?(?:<[^>\n]*>[ \t]*)?\(",
    _MEMBER,
)
_BRACE_LANGUAGES: dict[str, tuple] = {
    ".go": _GO, ".kt": _KOTLIN, ".kts": _KOTLIN, ".java": (_MEMBER,),
}
for _extension in (".js", ".jsx", ".ts", ".tsx", ".mjs", ".mts"):
    _BRACE_LANGUAGES[_extension] = _JAVASCRIPT


def _is_counted(line: str) -> bool:
    return bool(line.strip()) and not line.strip().startswith("#")


def _python_body_length(node: ast.AST, lines: list[str]) -> int:
    has_docstring = ast.get_docstring(node) is not None
    body = node.body[1:] if has_docstring else node.body
    if not body:
        return 0
    span = lines[body[0].lineno - 1:node.end_lineno]
    return sum(1 for line in span if _is_counted(line))


def _python_function_lengths(code: str) -> list[tuple[str, int]]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    lines = code.splitlines()
    return [
        (node.name, _python_body_length(node, lines))
        for node in ast.walk(tree) if isinstance(node, _PYTHON_FUNCTIONS)
    ]


def _blank_out(literal: re.Match) -> str:
    return re.sub(r"[^\n]", " ", literal.group())


def _closing_index(code: str, opening: int, pair: str) -> int:
    depth = 0
    for index in range(opening, len(code)):
        depth += {pair[0]: 1, pair[1]: -1}.get(code[index], 0)
        if depth == 0:
            return index
    return len(code)


def _is_definition(found: re.Match) -> bool:
    prefix = found.groupdict().get("prefix") or ""
    words = {found.group("name"), *prefix.split()}
    return not words & _NOT_DEFINITIONS


def _brace_body_length(code: str, found: re.Match) -> Optional[int]:
    if not _is_definition(found):
        return None
    parameters_end = _closing_index(code, found.end() - 1, "()")
    opening = _BODY_OPENING.match(code, parameters_end + 1)
    if opening is None:
        return None
    body_start = opening.end() - 1
    body = code[body_start + 1:_closing_index(code, body_start, "{}")]
    return sum(1 for line in body.split("\n") if line.strip())


def _brace_function_lengths(code: str, patterns: tuple) -> Iterator[tuple[str, int]]:
    # With comments and strings blanked, a line that held only a comment
    # counts as blank, and every brace left opens or closes a block.
    code = _LITERALS.sub(_blank_out, code)
    for pattern in patterns:
        for found in re.finditer(pattern, code, re.MULTILINE):
            length = _brace_body_length(code, found)
            if length is not None:
                yield found.group("name"), length


def function_lengths(code: str, file_path: str) -> list[tuple[str, int]]:
    """Return each function in code with the number of lines in its body.

    Blank lines, comment lines, and a Python docstring are not counted.
    Python is read through its syntax tree. Go, JavaScript, TypeScript, Java,
    and Kotlin are read with patterns, which find a function only when its
    body opens with a brace after the parameter list. A file in any other
    language, or Python that does not parse, gives an empty list.
    """
    extension = os.path.splitext(file_path)[1].lower()
    if extension == ".py":
        return _python_function_lengths(code)
    patterns = _BRACE_LANGUAGES.get(extension, ())
    return list(_brace_function_lengths(code, patterns))


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
    """
    if not _is_guarded_file(file_path) or not Path(file_path).is_file():
        return
    current_text = read_text(file_path)
    edited_text = apply_edit(current_text, old_string, new_string, replace_all)
    accepted = _longest_by_name(function_lengths(current_text, file_path))
    added = _over_limit(function_lengths(edited_text, file_path), accepted)
    if added:
        _block_added(file_path, added)
