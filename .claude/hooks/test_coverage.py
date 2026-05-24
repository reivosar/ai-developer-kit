#!/usr/bin/env python3
"""Coverage measurement for hook modules using the coverage API."""
import importlib.util
import os
import sys

HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HOOKS_DIR)

try:
    import coverage
except ImportError:
    print("coverage not installed — run: pip install coverage")
    sys.exit(1)

SOURCES = [
    os.path.join(HOOKS_DIR, "hook_lib.py"),
    os.path.join(HOOKS_DIR, "bash_guard.py"),
    os.path.join(HOOKS_DIR, "git_guard.py"),
    os.path.join(HOOKS_DIR, "cp_guard.py"),
    os.path.join(HOOKS_DIR, "pre_bash_check.py"),
    os.path.join(HOOKS_DIR, "pre-bash-check.py"),
    os.path.join(HOOKS_DIR, "pre-edit-check.py"),
    os.path.join(HOOKS_DIR, "pre-write-check.py"),
    os.path.join(HOOKS_DIR, "pre-worktree-check.py"),
    os.path.join(HOOKS_DIR, "env_file_guard.py"),
]

cov = coverage.Coverage(
    source=[HOOKS_DIR],
    include=SOURCES,
    omit=["*test*", "*/__pycache__/*"],
)
cov.start()

def _run(name: str, path: str) -> None:
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except SystemExit:
        pass

_run("test_hook_lib", os.path.join(HOOKS_DIR, "test_hook_lib.py"))
_run("test_allow_list", os.path.join(HOOKS_DIR, "test_allow_list.py"))
_run("test_pre_edit_check", os.path.join(HOOKS_DIR, "test_pre_edit_check.py"))
_run("test_pre_worktree_check", os.path.join(HOOKS_DIR, "test_pre_worktree_check.py"))

cov.stop()
cov.save()

print("\n=== Coverage Report ===")
cov.report(show_missing=True, skip_covered=False)
