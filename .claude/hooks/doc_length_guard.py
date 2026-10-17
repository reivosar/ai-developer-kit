#!/usr/bin/env python3
"""Guard: block Markdown documents that would exceed the line limit."""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hook_lib import apply_edit, block, read_text  # noqa: E402

LINE_LIMIT = 200
DOCUMENT_SUFFIX = ".md"


def _is_guarded_document(file_path: str) -> bool:
    if os.environ.get("DOC_LENGTH_GUARD_DISABLE"):
        return False
    return file_path.lower().endswith(DOCUMENT_SUFFIX)


def _count_lines(text: str) -> int:
    return len(text.splitlines())


def _grows_past_limit(current_count: int, edited_count: int) -> bool:
    return edited_count > max(LINE_LIMIT, current_count)


def _block_over_limit(file_path: str, line_count: int) -> None:
    block(
        f"'{os.path.basename(file_path)}' would have {line_count} lines,"
        f" exceeding the {LINE_LIMIT}-line document limit.",
        "Split the document by responsibility or shorten it.",
    )


def check_write(file_path: str, content: str) -> None:
    """Block a Write that creates a document longer than LINE_LIMIT."""
    if not _is_guarded_document(file_path):
        return
    line_count = _count_lines(content)
    if _grows_past_limit(current_count=0, edited_count=line_count):
        _block_over_limit(file_path, line_count)


def check_edit(
    file_path: str, old_string: str, new_string: str, replace_all: bool = False
) -> None:
    """Block an Edit that grows a document past LINE_LIMIT.

    An edit that shortens a document already over the limit is allowed,
    so an oversized document can be trimmed in several steps.

    Args:
        file_path: the file the Edit changes.
        old_string: the text the Edit replaces.
        new_string: the text it puts in its place.
        replace_all: whether every occurrence of old_string is replaced.
    """
    if not _is_guarded_document(file_path) or not Path(file_path).is_file():
        return
    current_text = read_text(file_path)
    edited_text = apply_edit(current_text, old_string, new_string, replace_all)
    edited_count = _count_lines(edited_text)
    if _grows_past_limit(_count_lines(current_text), edited_count):
        _block_over_limit(file_path, edited_count)
