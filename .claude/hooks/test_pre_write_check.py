#!/usr/bin/env python3
"""Tests for pre-write-check.py: blocks Write when target file already exists."""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(__file__), "pre-write-check.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("pre_write_check", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_hook(file_path_value, raw_stdin=None):
    if raw_stdin is None:
        payload = json.dumps({"tool_name": "Write", "tool_input": {"file_path": file_path_value}})
    else:
        payload = raw_stdin
    result = subprocess.run(
        ["python3", HOOK],
        input=payload, capture_output=True, text=True,
    )
    return result.returncode


passed = failed = 0


def check(label, got, expected):
    global passed, failed
    ok = got == expected
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {label} → expected exit {expected}, got {got}")
    if ok:
        passed += 1
    else:
        failed += 1


# Unit tests via importlib: read_file_path()
mod = _load_module()

import io, unittest.mock

with unittest.mock.patch("sys.stdin", io.StringIO('{"tool_input": {"file_path": "/tmp/foo.py"}}')):
    result_path = mod.read_file_path()
ok = result_path == "/tmp/foo.py"
print(f"[{'PASS' if ok else 'FAIL'}] read_file_path valid JSON → '/tmp/foo.py'")
if ok:
    passed += 1
else:
    failed += 1

with unittest.mock.patch("sys.stdin", io.StringIO("{}")):
    result_path = mod.read_file_path()
ok = result_path == ""
print(f"[{'PASS' if ok else 'FAIL'}] read_file_path missing key → ''")
if ok:
    passed += 1
else:
    failed += 1

with unittest.mock.patch("sys.stdin", io.StringIO("not-json")):
    result_path = mod.read_file_path()
ok = result_path is None
print(f"[{'PASS' if ok else 'FAIL'}] read_file_path malformed JSON → None")
if ok:
    passed += 1
else:
    failed += 1

print()

# Unit tests: is_blocked_env_file
for path, expect in [
    (".env",            True),
    (".env.local",      True),
    (".env.production", True),
    (".env.sample",     False),
    (".env.example",    False),
    ("src/app.py",      False),
]:
    ok = mod.is_blocked_env_file(path) == expect
    print(f"[{'PASS' if ok else 'FAIL'}] is_blocked_env_file({path!r}) == {expect}")
    if ok:
        passed += 1
    else:
        failed += 1

print()

# Blackbox tests: TC-WR-*
# TC-WR-01: nonexistent path → allowed
check("TC-WR-01 nonexistent file allowed", run_hook("/nonexistent/path/xyz.py"), 0)

# TC-WR-02: existing file → blocked
with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
    existing = f.name
try:
    check("TC-WR-02 existing file blocked", run_hook(existing), 2)
finally:
    os.unlink(existing)

# TC-WR-03: empty file_path → allowed (main() exits 0 on falsy path)
check("TC-WR-03 empty path allowed", run_hook(""), 0)

# TC-WR-04: malformed JSON stdin → allowed (exception caught, returns None, exits 0)
check("TC-WR-04 malformed JSON allowed", run_hook(None, raw_stdin="not-json"), 0)

# TC-WR-05: path to an existing directory → blocked (os.path.exists is True for dirs)
tmpdir = tempfile.mkdtemp()
try:
    check("TC-WR-05 existing directory blocked", run_hook(tmpdir), 2)
finally:
    os.rmdir(tmpdir)

# TC-ENV-PW-01: Write .env → blocked
check("TC-ENV-PW-01 Write .env blocked", run_hook(".env"), 2)

# TC-ENV-PW-02: Write .env.local → blocked
check("TC-ENV-PW-02 Write .env.local blocked", run_hook(".env.local"), 2)

# TC-ENV-PW-03: Write .env.sample → allowed (new file, not blocked by env check)
check("TC-ENV-PW-03 Write .env.sample allowed", run_hook(".env.sample"), 0)

# TC-ENV-PW-04: Write .env.example → allowed (use nonexistent absolute path)
_tmpdir_env = tempfile.mkdtemp()
try:
    check("TC-ENV-PW-04 Write .env.example allowed",
          run_hook(os.path.join(_tmpdir_env, ".env.example")), 0)
finally:
    shutil.rmtree(_tmpdir_env, ignore_errors=True)

print(f"\n{passed} passed, {failed} failed")
sys.exit(0 if failed == 0 else 1)
