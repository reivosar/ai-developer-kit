#!/usr/bin/env python3
"""Integration tests for pre-write.py: env guard, file-exists guard, content checks."""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(__file__), "pre-write.py")

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


# File guard tests
check("TC-WR-01 nonexistent file allowed", run("/nonexistent/path/xyz.py"), 0)

with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
    existing = f.name
try:
    check("TC-WR-02 existing file blocked", run(existing), 2)
finally:
    os.unlink(existing)

check("TC-WR-03 empty path allowed", run(""), 0)

# .env guard tests (use temp dirs to avoid hitting real files)
d1 = tempfile.mkdtemp()
try:
    check("TC-ENV-01 Write .env blocked",       run(os.path.join(d1, ".env")), 2)
    check("TC-ENV-02 Write .env.local blocked",  run(os.path.join(d1, ".env.local")), 2)
    check("TC-ENV-03 Write .env.sample allowed", run(os.path.join(d1, ".env.sample")), 0)
    check("TC-ENV-04 Write .env.example allowed",run(os.path.join(d1, ".env.example")), 0)
finally:
    shutil.rmtree(d1, ignore_errors=True)

# Content guard tests — build bad strings at runtime via chr()
_JP = chr(0x3053) + chr(0x3093) + chr(0x306b)    # hiragana
_EM = chr(0x1F600)                                  # emoji face
_ascii_path = "/tmp/nonexistent_test_file_x.py"

check("TC-CG-01 Japanese content blocked",
      run(_ascii_path, "hello " + _JP + " world"), 2)
check("TC-CG-02 emoji content blocked",
      run(_ascii_path, "nice " + _EM + " job"), 2)
check("TC-CG-03 ASCII content allowed",
      run(_ascii_path, "def hello(): pass"), 0)

print(f"\n{passed} passed, {failed} failed")
sys.exit(0 if failed == 0 else 1)
