#!/usr/bin/env python3
"""Start a blocking hook so that any error, even one while it loads, blocks.

Usage: run-hook.py <hook script in this directory>

settings.json starts the hooks that guard a tool call through this file.
It depends on fail_closed.py and the standard library only.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fail_closed  # noqa: E402

fail_closed.install()
fail_closed.run_entry_point(sys.argv[1])
