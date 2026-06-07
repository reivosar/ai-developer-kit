#!/usr/bin/env python3
"""Detects prompt injection patterns in user input."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_lib  # noqa: E402

_INJECTION_RE = re.compile(
    r"ignore\s+(all\s+)?(previous|prior)?\s*instructions?"
    r"|disregard\s+(all\s+)?(your\s+|the\s+)?(previous\s+|prior\s+)?instructions?"
    r"|forget\s+(everything|all|your\s+instructions?)"
    r"|you\s+are\s+now\b"
    r"|act\s+as\s+(a\s+|an\s+|the\s+)?\w"
    r"|new\s+instructions?"
    r"|\[system\]"
    r"|<system\b",
    re.IGNORECASE,
)


def check_injection(prompt: str) -> None:
    if _INJECTION_RE.search(prompt):
        hook_lib.block(
            "Prompt injection pattern detected.",
            "Input contains instructions that attempt to override agent directives.",
        )
