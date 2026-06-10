#!/usr/bin/env python3
"""Tests for block-read.sh: PreToolUse[Read] no-op that allows the Read tool."""
import os
import stat
import subprocess

HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
BLOCK_READ = os.path.join(HOOKS_DIR, "block-read.sh")

passed = failed = 0


def check(label: str, result: bool) -> None:
    global passed, failed
    status = "PASS" if result else "FAIL"
    print(f"[{status}] {label}")
    if result:
        passed += 1
    else:
        failed += 1


# TC-BLOCK-READ-01: block-read.sh exists
check("TC-BLOCK-READ-01 block-read.sh exists", os.path.isfile(BLOCK_READ))

# TC-BLOCK-READ-02: block-read.sh is executable
if os.path.isfile(BLOCK_READ):
    mode = os.stat(BLOCK_READ).st_mode
    executable = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    check("TC-BLOCK-READ-02 block-read.sh is executable", bool(mode & executable))
else:
    check("TC-BLOCK-READ-02 block-read.sh is executable", False)

# TC-BLOCK-READ-03: block-read.sh exits 0 so the Read tool is allowed
if os.path.isfile(BLOCK_READ):
    result = subprocess.run(["bash", BLOCK_READ], capture_output=True)
    check("TC-BLOCK-READ-03 block-read.sh exits 0 (Read allowed)", result.returncode == 0)
    # TC-BLOCK-READ-04: no BLOCKED message is emitted
    check(
        "TC-BLOCK-READ-04 block-read.sh emits no output",
        len(result.stdout) == 0 and len(result.stderr) == 0,
    )
else:
    check("TC-BLOCK-READ-03 block-read.sh exits 0 (Read allowed)", False)
    check("TC-BLOCK-READ-04 block-read.sh emits no output", False)

print(f"\n{passed} passed, {failed} failed")
raise SystemExit(0 if failed == 0 else 1)
