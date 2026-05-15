#!/usr/bin/env python3
"""Tests for pre-worktree-check.py: enforce that impl files are edited inside a worktree."""
import json
import os
import subprocess

HOOK = os.path.join(os.path.dirname(__file__), "pre-worktree-check.py")
WORKTREE_ABS = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "worktrees", "some-feature", "src", "app.py")
)

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

# TC-WT-02: markdown file → exit 0
check("TC-WT-02 markdown file", run_hook("README.md"), 0)

# TC-WT-03: json file → exit 0
check("TC-WT-03 json file", run_hook("config.json"), 0)

# TC-WT-04: shell file → exit 0
check("TC-WT-04 shell file", run_hook("deploy.sh"), 0)

# TC-WT-05: kit config path (hooks) → exit 0
check("TC-WT-05 kit hooks path", run_hook(".claude/hooks/foo.py"), 0)

# TC-WT-06: kit config path (skills) → exit 0
check("TC-WT-06 kit skills path", run_hook(".claude/skills/foo/SKILL.md"), 0)

# TC-WT-07: CLAUDE.md → exit 0
check("TC-WT-07 CLAUDE.md", run_hook("CLAUDE.md"), 0)

# TC-WT-08: impl file inside a worktree (absolute path) → exit 0
check("TC-WT-08 impl in worktree", run_hook(WORKTREE_ABS), 0)

# TC-WT-09: impl file in main repo (relative) → exit 2
check("TC-WT-09 impl in main repo .py", run_hook("src/app.py"), 2)

# TC-WT-10: impl file in main repo .ts (relative) → exit 2
check("TC-WT-10 impl in main repo .ts", run_hook("src/app.ts"), 2)

# TC-WT-11: Write tool, impl file not in worktree → exit 2
check("TC-WT-11 Write tool blocked", run_hook("lib/util.go", tool_name="Write"), 2)

print(f"\n{passed} passed, {failed} failed")
raise SystemExit(0 if failed == 0 else 1)
