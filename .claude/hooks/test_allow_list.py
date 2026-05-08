#!/usr/bin/env python3
"""Smoke-test the allow list changes in settings.json."""
import json, subprocess, sys, os

SETTINGS = os.path.join(os.path.dirname(__file__), "../settings.json")
HOOK = os.path.join(os.path.dirname(__file__), "pre-bash-check.py")

cases = [
    # (command, expect_blocked)
    ("git stash drop",        True),
    ("git stash clear",       True),
    ("git branch -D my-branch", True),
    ("git stash list",        False),
    ("git stash",             False),
    ("git stash push",        False),
    ("git stash pop",         False),
    ("git stash apply",       False),
    ("git stash show",        False),
    ("git branch",            False),
    ("git branch -d my-branch", False),
    ("git branch -a",         False),
    ("git branch -v",         False),
    ("git checkout --",       True),   # Stage-2 catch
]

passed = failed = 0
for cmd, expect_blocked in cases:
    payload = json.dumps({"tool_input": {"command": cmd}})
    result = subprocess.run(
        ["python3", HOOK, SETTINGS],
        input=payload, capture_output=True, text=True
    )
    blocked = result.returncode == 2
    ok = blocked == expect_blocked
    status = "PASS" if ok else "FAIL"
    label = "blocked" if expect_blocked else "allowed"
    print(f"[{status}] {cmd!r:40s} → expected {label}, got {'blocked' if blocked else 'allowed'}")
    if ok:
        passed += 1
    else:
        failed += 1

print(f"\n{passed} passed, {failed} failed")
sys.exit(0 if failed == 0 else 1)
