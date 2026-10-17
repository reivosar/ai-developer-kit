"""Tests that every module of the kit's own hooks carries fitting doc comments."""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from doc_comment_guard import find_violations  # noqa: E402

HOOKS_DIR = Path(__file__).parent
# The kit's own hooks are held to the rule one module at a time, so a failure
# names the module. A new hook module fails the list test until it is added.
HOOK_MODULES = [
    "anomaly_guard.py", "audit_log.py", "bash_guard.py", "commit_guard.py",
    "conftest.py", "content_guard.py", "coverage_guard.py", "coverage_runners.py", "cp_guard.py",
    "doc_comment_guard.py", "doc_comment_shapes.py", "doc_comments.py",
    "doc_length_guard.py", "dynamic_name_guard.py", "env_file_guard.py",
    "fail_closed.py", "find_guard.py", "function_definitions.py",
    "function_length_guard.py", "function_lengths.py", "git_guard.py", "git_option_guard.py",
    "hook_lib.py", "hook_records.py", "mcp_guard.py", "memory_guard.py",
    "post-tool.py", "pre-bash.py", "pre-edit.py", "pre-mcp.py", "pre-write.py",
    "prompt_injection_guard.py", "python_coverage.py", "python_doc_comments.py",
    "rate_limiter.py", "reference_notice.py", "run-hook.py",
    "static_analysis_guard.py", "tdd_guard.py", "template_guard.py",
    "testing_guard.py", "user-prompt-submit.py", "worktree_guard.py",
]


@pytest.mark.parametrize("module_name", HOOK_MODULES)
def test_find_violations_in_hook_module_returns_nothing(module_name: str):
    module = HOOKS_DIR / module_name
    assert find_violations(module.read_text(), module_name) == []


def test_hook_module_list_names_every_hook_module():
    modules = [
        path.name for path in HOOKS_DIR.glob("*.py") if not path.name.startswith("test_")
    ]
    assert HOOK_MODULES == sorted(modules)
