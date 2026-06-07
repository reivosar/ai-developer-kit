#!/usr/bin/env python3
"""Integration tests for pre-write.py: env guard, file-exists guard, content checks."""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(__file__), "pre-write.py")
HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))

passed = failed = 0


def check(label: str, got: int, expected: int) -> None:
    global passed, failed
    ok = got == expected
    print(f"[{'PASS' if ok else 'FAIL'}] {label} -> expected exit {expected}, got {got}")
    if ok:
        passed += 1
    else:
        failed += 1


def run(file_path: str, content: str = "") -> int:
    payload = json.dumps({"tool_name": "Write", "tool_input": {"file_path": file_path, "content": content}})
    env = {**os.environ, "WORKTREE_GUARD_DISABLE": "1"}
    r = subprocess.run(["python3", HOOK], input=payload, capture_output=True, text=True, env=env)
    return r.returncode


# File guard tests (paths must be inside the repo)
_nonexistent = os.path.join(HOOKS_DIR, "_nonexistent_test_xyz.py")
check("TC-WR-01 nonexistent file inside repo allowed", run(_nonexistent), 0)
check("TC-WR-02 existing file blocked", run(HOOK), 2)
check("TC-WR-03 empty path allowed", run(""), 0)

# .env guard tests (use hooks dir which is inside the repo)
check("TC-ENV-01 Write .env blocked",       run(os.path.join(HOOKS_DIR, ".env")), 2)
check("TC-ENV-02 Write .env.local blocked",  run(os.path.join(HOOKS_DIR, ".env.local")), 2)
check("TC-ENV-03 Write .env.sample allowed", run(os.path.join(HOOKS_DIR, ".env.sample")), 0)
check("TC-ENV-04 Write .env.example allowed",run(os.path.join(HOOKS_DIR, ".env.example")), 0)

# Outside-repo guard tests
check("TC-ORP-01 Write to /tmp/ blocked",
      run("/tmp/throwaway_script.py", "print('hi')"), 2)
check("TC-ORP-02 Write to /var/tmp/ blocked",
      run("/var/tmp/foo.py", "x = 1"), 2)

# Content guard tests — build bad strings at runtime via chr()
_JP = chr(0x3053) + chr(0x3093) + chr(0x306b)    # hiragana
_EM = chr(0x1F600)                                  # emoji face
_repo_nonexistent = os.path.join(os.path.dirname(__file__), "_nonexistent_test_x.py")

check("TC-CG-01 Japanese content blocked",
      run(_repo_nonexistent, "hello " + _JP + " world"), 2)
check("TC-CG-02 emoji content blocked",
      run(_repo_nonexistent, "nice " + _EM + " job"), 2)
check("TC-CG-03 ASCII content allowed",
      run(_repo_nonexistent, "def hello(): pass"), 0)

print(f"\n{passed} passed, {failed} failed")
sys.exit(0 if failed == 0 else 1)
