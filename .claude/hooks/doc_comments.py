#!/usr/bin/env python3
"""Find the public definitions in source text with their doc comment."""
import ast
import itertools
import os
import re
from typing import Iterator, NamedTuple, Optional

_NEVER = r"(?!)"
_PYTHON_DEFINITIONS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
# A setter or an overload is documented on the definition it belongs to.
_DOCUMENTED_ELSEWHERE = {"setter", "deleter", "overload", "override"}
_BLOCK_BOUNDARY = re.compile(r"^\s*$|[;{}]\s*$")


class Definition(NamedTuple):
    """A public function, method, or type as the doc comment rules see it."""

    name: str
    doc: Optional[str]  # None when the definition has no doc comment
    params: Optional[tuple]  # None when the parameters cannot be read


class _Language(NamedTuple):
    definitions: tuple  # regexes with a group "name"; one ending in "(" is callable
    param_name: Optional[str] = None  # regex with a group "name", per parameter
    doc_prefix: Optional[str] = None  # the doc comment is a run of such lines
    inherits_doc: str = _NEVER  # marks a definition documented where it is declared


_ANNOTATIONS = r"^[ \t]*(?:@\w+(?:\([^)\n]*\))?[ \t]+)*"
_JAVA = _Language(
    definitions=(
        _ANNOTATIONS
        + r"public\b[^;{=()\n]*?\b(?:class|interface|enum)[ \t]+(?P<name>\w+)",
        _ANNOTATIONS + r"public\b[^;{=()\n]*?\b(?P<name>\w+)[ \t]*\(",
    ),
    param_name=r"(?P<name>\w+)[ \t]*(?:\[\])*$",
    inherits_doc=r"@Override\b",
)
_KOTLIN_MODIFIERS = (
    r"^[ \t]*(?:(?:public|open|abstract|final|suspend|inline|operator|infix"
    r"|tailrec|external|data|sealed|enum|annotation|value)[ \t]+)*"
)
_KOTLIN = _Language(
    definitions=(
        _KOTLIN_MODIFIERS + r"(?:class|interface|object)[ \t]+(?P<name>\w+)",
        _KOTLIN_MODIFIERS
        + r"fun[ \t]+(?:<[^>\n]+>[ \t]+)?(?:[\w<>?,.]+\.)?(?P<name>\w+)[ \t]*\(",
    ),
    param_name=(
        r"^(?:@\w+[ \t]+)*(?:(?:vararg|noinline|crossinline|val|var)[ \t]+)*"
        r"(?P<name>\w+)[ \t]*:"
    ),
)
_GO = _Language(
    definitions=(
        r"^type[ \t]+(?P<name>[A-Z]\w*)\b",
        r"^func[ \t]+(?:\([^)\n]*\)[ \t]*)?(?P<name>[A-Z]\w*)[ \t]*[(\[]",
    ),
    doc_prefix="//",
)
_RUST_QUALIFIERS = r'(?:(?:async|const|unsafe|extern(?:[ \t]+"[^"\n]*")?)[ \t]+)*'
_RUST = _Language(
    definitions=(
        r"^[ \t]*pub[ \t]+(?:struct|enum|trait|union)[ \t]+(?P<name>\w+)",
        r"^[ \t]*pub[ \t]+" + _RUST_QUALIFIERS
        + r"fn[ \t]+(?P<name>\w+)[ \t]*(?:<[^(\n]*>)?[ \t]*\(",
    ),
    doc_prefix="///",
)
_JS_NAME = r"(?P<name>[A-Za-z_$][\w$]*)[ \t]*"
_JS_CALL = r"(?:<[^>\n]*>)?[ \t]*\("
_JAVASCRIPT = _Language(
    definitions=(
        r"^export[ \t]+(?:default[ \t]+)?(?:abstract[ \t]+)?class[ \t]+" + _JS_NAME,
        r"^export[ \t]+(?:default[ \t]+)?(?:async[ \t]+)?function\*?[ \t]+"
        + _JS_NAME + _JS_CALL,
        r"^export[ \t]+(?:const|let)[ \t]+" + _JS_NAME
        + r"(?::[^=\n]+)?=[ \t]*(?:async[ \t]*)?" + _JS_CALL,
        r"^[ \t]+public[ \t]+(?:(?:static|async|override|abstract)[ \t]+)*"
        + _JS_NAME + _JS_CALL,
    ),
    param_name=(
        r"^(?:(?:public|private|protected|readonly|override)[ \t]+)*"
        r"(?:\.\.\.)?(?P<name>[A-Za-z_$][\w$]*)"
    ),
    inherits_doc=r"\boverride\b",
)

_LANGUAGES: dict[str, _Language] = {
    ".java": _JAVA, ".kt": _KOTLIN, ".kts": _KOTLIN, ".go": _GO, ".rs": _RUST,
}
for _extension in (".js", ".jsx", ".ts", ".tsx", ".mjs", ".mts"):
    _LANGUAGES[_extension] = _JAVASCRIPT


def _decorator_name(decorator: ast.expr) -> str:
    target = decorator.func if isinstance(decorator, ast.Call) else decorator
    if isinstance(target, ast.Attribute):
        return target.attr
    return target.id if isinstance(target, ast.Name) else ""


def _is_documented_elsewhere(node: ast.AST) -> bool:
    names = {_decorator_name(decorator) for decorator in node.decorator_list}
    return bool(names & _DOCUMENTED_ELSEWHERE)


def _python_parameters(node: ast.AST) -> Optional[tuple]:
    if isinstance(node, ast.ClassDef):
        return None
    arguments = node.args
    named = arguments.posonlyargs + arguments.args + arguments.kwonlyargs
    collectors = [arguments.vararg, arguments.kwarg]
    names = [argument.arg for argument in named + collectors if argument]
    return tuple(name for name in names if name not in ("self", "cls"))


def _public_python_nodes(nodes: list, prefix: str) -> Iterator[Definition]:
    for node in nodes:
        if not isinstance(node, _PYTHON_DEFINITIONS) or node.name.startswith("_"):
            continue
        if _is_documented_elsewhere(node):
            continue
        name = prefix + node.name
        yield Definition(name, ast.get_docstring(node), _python_parameters(node))
        if isinstance(node, ast.ClassDef):
            yield from _public_python_nodes(node.body, name + ".")


def _python_definitions(code: str) -> list[Definition]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    return list(_public_python_nodes(tree.body, ""))


def _block_comment_ending_at(lines: list[str], end: int) -> Optional[str]:
    for start in range(end, -1, -1):
        if "/*" in lines[start]:
            comment = "\n".join(lines[start:end + 1]).strip()
            return comment if comment.startswith("/**") else None
    return None


def _block_doc(lines_above: list[str]) -> Optional[str]:
    # Annotations may sit between the comment and the definition, so the
    # search runs upward until a line that ends another statement.
    for index in range(len(lines_above) - 1, -1, -1):
        line = lines_above[index].rstrip()
        if line.endswith("*/"):
            return _block_comment_ending_at(lines_above, index)
        if _BLOCK_BOUNDARY.search(line):
            return None
    return None


def _line_doc(lines_above: list[str], prefix: str) -> Optional[str]:
    # A Rust attribute such as #[derive(Debug)] may sit between the comment
    # and the item it documents.
    below_attributes = itertools.dropwhile(
        lambda line: line.lstrip().startswith("#["), reversed(lines_above)
    )
    comment_lines = itertools.takewhile(
        lambda line: line.lstrip().startswith(prefix), below_attributes
    )
    text = [line.lstrip()[len(prefix):].strip() for line in comment_lines]
    return "\n".join(reversed(text)) or None


def _doc(lines_above: list[str], language: _Language) -> Optional[str]:
    if language.doc_prefix:
        return _line_doc(lines_above, language.doc_prefix)
    return _block_doc(lines_above)


def _inherits_doc(
    lines_above: list[str], definition_line: str, language: _Language
) -> bool:
    annotations = itertools.takewhile(
        lambda line: line.lstrip().startswith("@"), reversed(lines_above)
    )
    return any(
        re.search(language.inherits_doc, line)
        for line in [definition_line, *annotations]
    )


def _depth_change(char: str, previous: str, depth: int) -> int:
    opens_generic = char == "<" and (previous.isalnum() or previous == "_")
    closes_generic = char == ">" and depth > 0 and previous not in "=-"
    if char in "([{" or opens_generic:
        return 1
    if char in ")]}" or closes_generic:
        return -1
    return 0


def _split_parameters(text: str) -> list[str]:
    pieces, depth, previous = [""], 0, " "
    for char in text:
        depth += _depth_change(char, previous, depth)
        if char == "," and depth == 0:
            pieces.append("")
        else:
            pieces[-1] += char
        previous = char
    return [piece.strip() for piece in pieces if piece.strip()]


def _closing_parenthesis(code: str, opening: int) -> int:
    depth = 0
    for index in range(opening, len(code)):
        depth += {"(": 1, ")": -1}.get(code[index], 0)
        if depth == 0:
            return index
    return len(code)


def _parameters(
    code: str, found: re.Match, language: _Language
) -> Optional[tuple]:
    if language.param_name is None or not found.group(0).endswith("("):
        return None
    opening = found.end() - 1
    closing = _closing_parenthesis(code, opening)
    pieces = _split_parameters(code[opening + 1:closing])
    names = [re.search(language.param_name, piece) for piece in pieces]
    if not all(names):
        return None
    return tuple(name.group("name") for name in names)


def _definition_at(
    code: str, lines: list[str], found: re.Match, language: _Language
) -> Optional[Definition]:
    line_index = code.count("\n", 0, found.start())
    lines_above = lines[:line_index]
    if _inherits_doc(lines_above, lines[line_index], language):
        return None
    parameters = _parameters(code, found, language)
    return Definition(found.group("name"), _doc(lines_above, language), parameters)


def _pattern_definitions(code: str, language: _Language) -> list[Definition]:
    lines = code.split("\n")
    matches = [
        found for pattern in language.definitions
        for found in re.finditer(pattern, code, re.MULTILINE)
    ]
    matches.sort(key=lambda found: found.start())
    definitions = [
        _definition_at(code, lines, found, language) for found in matches
    ]
    return [definition for definition in definitions if definition]


def find_public_definitions(code: str, file_path: str) -> list[Definition]:
    """Return the public definitions in code, in source order.

    Python is read through its syntax tree. Go, JavaScript, TypeScript, Rust,
    Java, and Kotlin are read with patterns, which find a definition only
    when its visibility is written on the definition line. A file in any
    other language, or Python that does not parse, gives an empty list.
    """
    extension = os.path.splitext(file_path)[1].lower()
    if extension == ".py":
        return _python_definitions(code)
    language = _LANGUAGES.get(extension)
    return _pattern_definitions(code, language) if language else []
