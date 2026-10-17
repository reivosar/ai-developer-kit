#!/usr/bin/env python3
"""Measure the body of each function in source text, per language."""
import ast
import os
import re
from typing import Iterator, NamedTuple, Optional

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
_RUST = (
    r"^[ \t]*(?:pub(?:\([^)\n]*\))?[ \t]+)?"
    r"(?:(?:default|async|const|unsafe|extern)[ \t]+)*"
    r"fn[ \t]+(?P<name>\w+)[ \t]*(?:<[^(\n]*>)?[ \t]*\(",
)
# In Rust a quote also starts a lifetime ('a), so a character literal is one
# character or one escape between quotes, and a string may span lines.
_RUST_LITERALS = re.compile(
    r"""//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|'(?:\\.[^'\n]*|[^'\\\n])'""",
    re.DOTALL,
)
# A Rust signature may hold "=" in a bound such as Iterator<Item = u32>.
_RUST_BODY_OPENING = re.compile(r"[^;{}]*?\{")


class _BraceLanguage(NamedTuple):
    patterns: tuple  # regexes with a group "name" that end at the "("
    literals: re.Pattern = _LITERALS
    body_opening: re.Pattern = _BODY_OPENING


_GO_LANGUAGE = _BraceLanguage(_GO)
_KOTLIN_LANGUAGE = _BraceLanguage(_KOTLIN)
_BRACE_LANGUAGES: dict[str, _BraceLanguage] = {
    ".go": _GO_LANGUAGE, ".kt": _KOTLIN_LANGUAGE, ".kts": _KOTLIN_LANGUAGE,
    ".java": _BraceLanguage((_MEMBER,)),
    ".rs": _BraceLanguage(_RUST, _RUST_LITERALS, _RUST_BODY_OPENING),
}
for _extension in (".js", ".jsx", ".ts", ".tsx", ".mjs", ".mts"):
    _BRACE_LANGUAGES[_extension] = _BraceLanguage(_JAVASCRIPT)


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


def _brace_body_length(
    code: str, found: re.Match, body_opening: re.Pattern
) -> Optional[int]:
    if not _is_definition(found):
        return None
    parameters_end = _closing_index(code, found.end() - 1, "()")
    opening = body_opening.match(code, parameters_end + 1)
    if opening is None:
        return None
    body_start = opening.end() - 1
    body = code[body_start + 1:_closing_index(code, body_start, "{}")]
    return sum(1 for line in body.split("\n") if line.strip())


def _brace_function_lengths(
    code: str, language: _BraceLanguage
) -> Iterator[tuple[str, int]]:
    # With comments and strings blanked, a line that held only a comment
    # counts as blank, and every brace left opens or closes a block.
    code = language.literals.sub(_blank_out, code)
    for pattern in language.patterns:
        for found in re.finditer(pattern, code, re.MULTILINE):
            length = _brace_body_length(code, found, language.body_opening)
            if length is not None:
                yield found.group("name"), length


def function_lengths(code: str, file_path: str) -> list[tuple[str, int]]:
    """Return each function in code with the number of lines in its body.

    Blank lines, comment lines, and a Python docstring are not counted.
    Python is read through its syntax tree. Go, JavaScript, TypeScript, Java,
    Kotlin, and Rust are read with patterns, which find a function only when
    its body opens with a brace after the parameter list. A file in any other
    language, or Python that does not parse, gives an empty list.

    Args:
        code: the source text.
        file_path: the file's path; its extension picks the language.
    """
    extension = os.path.splitext(file_path)[1].lower()
    if extension == ".py":
        return _python_function_lengths(code)
    language = _BRACE_LANGUAGES.get(extension)
    return list(_brace_function_lengths(code, language)) if language else []
