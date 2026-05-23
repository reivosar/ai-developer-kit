#!/usr/bin/env python3
"""Tests for pre-worktree-check.py: enforce that ALL file edits happen inside a worktree."""
import json
import os
import sys
import subprocess

from pathlib import Path
sys.path.insert(0, os.path.dirname(__file__))
from hook_lib import REPO_ROOT, WORKTREES_DIR  # noqa: E402

HOOK = os.path.join(os.path.dirname(__file__), "pre-worktree-check.py")
IN_WORKTREE = str(WORKTREES_DIR / "some-feature" / "src" / "app.py")
OUTSIDE = {
    "readme":  str(REPO_ROOT / "README.md"),
    "json":    str(REPO_ROOT / "config.json"),
    "shell":   str(REPO_ROOT / "deploy.sh"),
    "hooks":   str(REPO_ROOT / ".claude" / "hooks" / "foo.py"),
    "skills":  str(REPO_ROOT / ".claude" / "skills" / "foo" / "SKILL.md"),
    "claude":  str(REPO_ROOT / "CLAUDE.md"),
    "py":      str(REPO_ROOT / "src" / "app.py"),
    "ts":      str(REPO_ROOT / "src" / "app.ts"),
    "go":      str(REPO_ROOT / "lib" / "util.go"),
}

TRASH_FILE   = str(REPO_ROOT / ".trash" / "20240101-120000" / "app.py")
PLAN_FILE    = str(REPO_ROOT / ".claude" / "plan" / "plan.md")
MEMORY_FILE  = str(Path.home() / ".claude" / "projects" / "some-project" / "memory" / "user.md")

passed = failed = 0


def run_hook(file_path: str, tool_name: str = "Edit") -> int:
    payload = json.dumps({"tool_name": tool_name, "tool_input": {"file_path": file_path}})
    result = subprocess.run(
        ["python3", HOOK],
        input=payload,
        capture_output=True,
        text=True,
    )
    return result.returncode


def check(label: str, got: int, expected: int) -> None:
    global passed, failed
    ok = got == expected
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {label} → expected exit {expected}, got {got}")
    if ok:
        passed += 1
    else:
        failed += 1


# TC-WT-01: empty file_path → exit 0
check("TC-WT-01 empty file_path", run_hook(""), 0)

# TC-WT-02: markdown file outside worktree → exit 2
check("TC-WT-02 markdown file", run_hook(OUTSIDE["readme"]), 2)

# TC-WT-03: json file outside worktree → exit 2
check("TC-WT-03 json file", run_hook(OUTSIDE["json"]), 2)

# TC-WT-04: shell file outside worktree → exit 2
check("TC-WT-04 shell file", run_hook(OUTSIDE["shell"]), 2)

# TC-WT-05: kit config path (hooks) outside worktree → exit 2
check("TC-WT-05 kit hooks path", run_hook(OUTSIDE["hooks"]), 2)

# TC-WT-06: kit config path (skills) outside worktree → exit 2
check("TC-WT-06 kit skills path", run_hook(OUTSIDE["skills"]), 2)

# TC-WT-07: CLAUDE.md outside worktree → exit 2
check("TC-WT-07 CLAUDE.md", run_hook(OUTSIDE["claude"]), 2)

# TC-WT-08: impl file inside a worktree (absolute path) → exit 0
check("TC-WT-08 impl in worktree", run_hook(IN_WORKTREE), 0)

# TC-WT-09: impl file in main repo .py → exit 2
check("TC-WT-09 impl in main repo .py", run_hook(OUTSIDE["py"]), 2)

# TC-WT-10: impl file in main repo .ts → exit 2
check("TC-WT-10 impl in main repo .ts", run_hook(OUTSIDE["ts"]), 2)

# TC-WT-11: Write tool, impl file not in worktree → exit 2
check("TC-WT-11 Write tool blocked", run_hook(OUTSIDE["go"], tool_name="Write"), 2)

# TC-WT-12: .trash file → exit 0
check("TC-WT-12 .trash file allowed", run_hook(TRASH_FILE), 0)

# TC-WT-13: .claude/plan file → exit 0
check("TC-WT-13 .claude/plan file allowed", run_hook(PLAN_FILE), 0)

# TC-WT-14: memory file (outside repo) → exit 0
check("TC-WT-14 memory file allowed", run_hook(MEMORY_FILE), 0)

print(f"\n{passed} passed, {failed} failed")
raise SystemExit(0 if failed == 0 else 1)
