#!/usr/bin/env python3
"""Tests for hook_lib.py: REPO_ROOT, WORKTREES_DIR, read_stdin_json, block."""
import io
import json
import os
import subprocess
import sys
import importlib.util

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

# TC-LIB-05: read_stdin_json returns dict from valid JSON
_orig_stdin = sys.stdin
sys.stdin = io.TextIOWrapper(io.BytesIO(json.dumps({"tool_input": {"command": "git status"}}).encode()))
result = mod.read_stdin_json()
sys.stdin = _orig_stdin
check("TC-LIB-05 read_stdin_json returns dict", isinstance(result, dict))
check("TC-LIB-06 read_stdin_json parses keys", result.get("tool_input", {}).get("command") == "git status")

# TC-LIB-07: read_stdin_json returns empty dict on invalid JSON
sys.stdin = io.TextIOWrapper(io.BytesIO(b"not-json"))
result = mod.read_stdin_json()
sys.stdin = _orig_stdin
check("TC-LIB-07 read_stdin_json returns {} on bad input", result == {})

# TC-LIB-08: block() prints BLOCKED message and exits with code 2
script = (
    "import sys, importlib.util\n"
    f"spec = importlib.util.spec_from_file_location('hook_lib', {HOOK_LIB!r})\n"
    "mod = importlib.util.module_from_spec(spec)\n"
    "spec.loader.exec_module(mod)\n"
    "mod.block('test reason', 'detail line')\n"
)
proc = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
check("TC-LIB-08 block() exits with code 2", proc.returncode == 2)
check("TC-LIB-09 block() prints BLOCKED prefix", "BLOCKED: test reason" in proc.stderr)
check("TC-LIB-10 block() prints detail lines", "detail line" in proc.stderr)

# TC-LIB-11: block() with no detail lines still exits 2
script2 = (
    "import sys, importlib.util\n"
    f"spec = importlib.util.spec_from_file_location('hook_lib', {HOOK_LIB!r})\n"
    "mod = importlib.util.module_from_spec(spec)\n"
    "spec.loader.exec_module(mod)\n"
    "mod.block('only reason')\n"
)
proc2 = subprocess.run([sys.executable, "-c", script2], capture_output=True, text=True)
check("TC-LIB-11 block() no detail lines exits 2", proc2.returncode == 2)
check("TC-LIB-12 block() no detail lines has BLOCKED", "BLOCKED: only reason" in proc2.stderr)

print(f"\n{passed} passed, {failed} failed")
raise SystemExit(0 if failed == 0 else 1)
