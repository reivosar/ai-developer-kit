#!/usr/bin/env python3
"""End-to-end tests for skill-selector dispatch marker enforcement."""
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from hook_lib import REPO_ROOT, WORKTREES_DIR  # noqa: E402

HOOK = os.path.join(os.path.dirname(__file__), "pre-worktree-check.py")
MARKER = REPO_ROOT / ".claude" / ".dispatched"
IN_WORKTREE = str(WORKTREES_DIR / "some-feature" / "src" / "app.py")

passed = failed = 0


def run_hook(file_path: str) -> int:
    payload = json.dumps({"tool_name": "Edit", "tool_input": {"file_path": file_path}})
    result = subprocess.run(["python3", HOOK], input=payload, capture_output=True, text=True)
    return result.returncode


def check(label: str, got: int, expected: int) -> None:
    global passed, failed
    ok = got == expected
    print(f"[{'PASS' if ok else 'FAIL'}] {label} → expected exit {expected}, got {got}")
    if ok:
        passed += 1
    else:
        failed += 1


# --- Setup: record original marker state ---
marker_existed = MARKER.exists()
MARKER.parent.mkdir(parents=True, exist_ok=True)

# E2E-01: marker absent → edit blocked
MARKER.unlink(missing_ok=True)
check("E2E-01 edit blocked when skill-selector not invoked", run_hook(IN_WORKTREE), 2)

# E2E-02: touch marker (simulates skill-selector Step 0) → edit allowed
MARKER.touch()
check("E2E-02 edit allowed after skill-selector invoked", run_hook(IN_WORKTREE), 0)

# E2E-03: marker absent → writing marker itself allowed (skill-selector can always create it)
MARKER.unlink(missing_ok=True)
check("E2E-03 skill-selector can write marker even without prior marker", run_hook(str(MARKER)), 0)

# E2E-04: verify touch .claude/.dispatched is in the allow list
allow_hook = os.path.join(os.path.dirname(__file__), "pre-bash-check.py")
payload = json.dumps({"tool_input": {"command": "touch .claude/.dispatched"}})
result = subprocess.run(["python3", allow_hook], input=payload, capture_output=True, text=True)
check("E2E-04 touch .claude/.dispatched is in allow list", result.returncode, 0)

# E2E-05: administrative paths bypass dispatch check even without marker
MARKER.unlink(missing_ok=True)
trash_path = str(REPO_ROOT / ".trash" / "20240101-120000" / "app.py")
check("E2E-05 trash path allowed without marker", run_hook(trash_path), 0)

plan_path = str(REPO_ROOT / ".claude" / "plan" / "plan.md")
check("E2E-06 plan path allowed without marker", run_hook(plan_path), 0)

# Restore marker state
if marker_existed:
    MARKER.touch()
else:
    MARKER.unlink(missing_ok=True)

print(f"\n{passed} passed, {failed} failed")
sys.exit(0 if failed == 0 else 1)
