#!/usr/bin/env python3
"""Shared .env file guard: imported by pre-write-check.py and pre-edit-check.py."""
import os

ALLOWED_ENV_FILES = {'.env.sample', '.env.example'}


def is_blocked_env_file(path: str) -> bool:
    basename = os.path.basename(path)
    if basename == '.env':
        return True
    if basename.startswith('.env.'):
        return basename not in ALLOWED_ENV_FILES
    return False
