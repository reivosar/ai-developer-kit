#!/usr/bin/env python3
"""Integration tests for pre-edit.py: TDD enforcement and env guard via Edit tool."""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(__file__), "pre-edit.py")

passed = failed = 0


def check(label: str, got: int, expected: int) -> None:
    global passed, failed
    ok = got == expected
    print(f"[{'PASS' if ok else 'FAIL'}] {label} -> expected exit {expected}, got {got}")
    if ok:
        passed += 1
    else:
        failed += 1


def make_git_repo() -> str:
    d = tempfile.mkdtemp(prefix="hook_test_edit_")
    subprocess.run(["git", "init", d], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=d, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=d, check=True, capture_output=True)
    init = os.path.join(d, "init.txt")
    with open(init, "w") as f:
        f.write("init\n")
    subprocess.run(["git", "add", "init.txt"], cwd=d, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=d, check=True, capture_output=True)
    return d


def stage(d: str, name: str, content: str) -> None:
    path = os.path.join(d, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    subprocess.run(["git", "add", name], cwd=d, check=True, capture_output=True)


def commit(d: str, name: str, content: str) -> None:
    stage(d, name, content)
    subprocess.run(["git", "commit", "-m", f"add {name}"], cwd=d, check=True, capture_output=True)


def run(d: str, file_path: str, old_string: str = "") -> int:
    payload = json.dumps({
        "tool_name": "Edit",
        "tool_input": {"file_path": file_path, "old_string": old_string, "new_string": ""},
    })
    r = subprocess.run(["python3", HOOK], input=payload, capture_output=True, text=True, cwd=d)
    return r.returncode


d = make_git_repo()
try:
    check("TC-ED-01 markdown skipped", run(d, "README.md", "any"), 0)
finally:
    shutil.rmtree(d, ignore_errors=True)

d = make_git_repo()
try:
    check("TC-ED-02 test file skipped", run(d, "tests/test_app.py", "def test_x():"), 0)
finally:
    shutil.rmtree(d, ignore_errors=True)

d = make_git_repo()
try:
    check("TC-ED-03 empty old_string skipped", run(d, "src/app.py", ""), 0)
finally:
    shutil.rmtree(d, ignore_errors=True)

d = make_git_repo()
try:
    check("TC-ED-04 no tests blocked", run(d, "src/app.py", "def calc():"), 2)
finally:
    shutil.rmtree(d, ignore_errors=True)

d = make_git_repo()
try:
    stage(d, "tests/test_calc.py", "def test_calc():\n    calc()\n")
    check("TC-ED-05 staged test covers func", run(d, "src/app.py", "def calc():"), 0)
finally:
    shutil.rmtree(d, ignore_errors=True)

d = make_git_repo()
try:
    stage(d, "tests/test_other.py", "def test_other():\n    other()\n")
    check("TC-ED-06 staged test missing func", run(d, "src/app.py", "def calc():"), 2)
finally:
    shutil.rmtree(d, ignore_errors=True)

d = make_git_repo()
try:
    commit(d, "tests/test_calc.py", "def test_calc():\n    calc()\n")
    check("TC-ED-07 last-commit test covers func", run(d, "src/app.py", "def calc():"), 0)
finally:
    shutil.rmtree(d, ignore_errors=True)

d = make_git_repo()
try:
    stage(d, "tests/test_app.py", "# placeholder\n")
    check("TC-ED-08 stem match fallback", run(d, "src/app.py", "x = 1\n"), 0)
finally:
    shutil.rmtree(d, ignore_errors=True)

d = make_git_repo()
try:
    stage(d, "tests/test_other.py", "# placeholder\n")
    check("TC-ED-09 no stem match blocked", run(d, "src/app.py", "x = 1\n"), 2)
finally:
    shutil.rmtree(d, ignore_errors=True)

d = make_git_repo()
try:
    check("TC-ENV-01 Edit .env blocked", run(d, ".env", "SECRET=abc"), 2)
finally:
    shutil.rmtree(d, ignore_errors=True)

d = make_git_repo()
try:
    check("TC-ENV-02 Edit .env.local blocked", run(d, ".env.local", "KEY=val"), 2)
finally:
    shutil.rmtree(d, ignore_errors=True)

d = make_git_repo()
try:
    check("TC-ENV-03 Edit .env.sample allowed", run(d, ".env.sample", "KEY=val"), 0)
finally:
    shutil.rmtree(d, ignore_errors=True)

print(f"\n{passed} passed, {failed} failed")
sys.exit(0 if failed == 0 else 1)
