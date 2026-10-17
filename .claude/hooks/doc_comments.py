#!/usr/bin/env python3
"""Find the public definitions in source text with their doc comment."""
import itertools
import os
import re
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from doc_comment_shapes import LANGUAGES, Definition, Language  # noqa: E402
from python_doc_comments import python_definitions  # noqa: E402

_BLOCK_BOUNDARY = re.compile(r"^\s*$|[;{}]\s*$")


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


def _doc(lines_above: list[str], language: Language) -> Optional[str]:
    if language.doc_prefix:
        return _line_doc(lines_above, language.doc_prefix)
    return _block_doc(lines_above)


def _inherits_doc(
    lines_above: list[str], definition_line: str, language: Language
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
    code: str, found: re.Match, language: Language
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
    code: str, lines: list[str], found: re.Match, language: Language
) -> Optional[Definition]:
    line_index = code.count("\n", 0, found.start())
    lines_above = lines[:line_index]
    if _inherits_doc(lines_above, lines[line_index], language):
        return None
    parameters = _parameters(code, found, language)
    return Definition(found.group("name"), _doc(lines_above, language), parameters)


def _pattern_definitions(code: str, language: Language) -> list[Definition]:
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
        return python_definitions(code)
    language = LANGUAGES.get(extension)
    return _pattern_definitions(code, language) if language else []
