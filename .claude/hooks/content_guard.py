#!/usr/bin/env python3
"""Content guards for file writes and edits."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_lib  # noqa: E402

_JAPANESE_RE = re.compile(
    r"[ぁ-ゟ"   # hiragana
    r"゠-ヿ"    # katakana
    r"一-鿿]"   # CJK unified ideographs
)

# Built with chr() so the source file contains no literal emoji bytes.
_EMOJI_RE = re.compile(
    "["
    + chr(0x1F300) + "-" + chr(0x1F9FF)  # misc symbols, emoticons, transport, etc.
    + chr(0x2600) + "-" + chr(0x27BF)    # misc symbols, dingbats
    + chr(0xFE0F)                          # variation selector-16 (emoji presentation)
    + "]"
)

_EXEMPT_PATH_RE = re.compile(r"(locale|i18n|fixtures)", re.IGNORECASE)


def check_japanese(content: str, file_path: str) -> None:
    if _EXEMPT_PATH_RE.search(file_path):
        return
    if _JAPANESE_RE.search(content):
        hook_lib.block(
            "Japanese characters detected in file content.",
            "All project files must be written in English.",
            f"File: {file_path}",
        )


def check_emoji(content: str, file_path: str) -> None:
    if _EMOJI_RE.search(content):
        hook_lib.block(
            "Emoji detected in file content.",
            "Never use emojis in files. Use plain text (e.g. 'Good:' / 'Bad:') instead.",
            f"File: {file_path}",
        )
