#!/usr/bin/env python3
"""Tests for hook_lib.py: shared REPO_ROOT and WORKTREES_DIR resolution."""
import os
import sys

HOOK_LIB = os.path.join(os.path.dirname(__file__), "hook_lib.py")

passed = failed = 0


def check(label: str, result: bool) -> None:
    global passed, failed
    status = "PASS" if result else "FAIL"
    print(f"[{status}] {label}")
    if result:
        passed += 1
    else:
        failed += 1


# Import hook_lib — will fail with ImportError if file doesn't exist
import importlib.util

spec = importlib.util.spec_from_file_location("hook_lib", HOOK_LIB)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# TC-LIB-01: REPO_ROOT is an existing directory
check("TC-LIB-01 REPO_ROOT exists", mod.REPO_ROOT.is_dir())

# TC-LIB-02: REPO_ROOT contains .claude/ (it's the git repo root)
check("TC-LIB-02 REPO_ROOT has .claude/", (mod.REPO_ROOT / ".claude").is_dir())

# TC-LIB-03: WORKTREES_DIR is REPO_ROOT/.claude/worktrees
check(
    "TC-LIB-03 WORKTREES_DIR path",
    mod.WORKTREES_DIR == mod.REPO_ROOT / ".claude" / "worktrees",
)

# TC-LIB-04: REPO_ROOT is absolute
check("TC-LIB-04 REPO_ROOT is absolute", mod.REPO_ROOT.is_absolute())

print(f"\n{passed} passed, {failed} failed")
raise SystemExit(0 if failed == 0 else 1)
