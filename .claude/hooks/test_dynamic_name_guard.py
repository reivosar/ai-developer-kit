"""Tests for dynamic_name_guard: names must not be assembled at runtime."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dynamic_name_guard  # noqa: E402

HOOKS_DIR = Path(__file__).parent
PY_ASSEMBLED = 'handler = getattr(self, "handle_" + kind)\n'
PY_LITERAL = 'handler = getattr(self, "handle_refund")\n'

ASSEMBLED_SAMPLES = [
    ("orders.py", PY_ASSEMBLED),
    ("orders.py", 'handler = getattr(self, f"handle_{kind}")\n'),
    ("orders.py", 'setattr(self, prefix + "_total", total)\n'),
    ("plugins.py", 'module = importlib.import_module("plugins." + name)\n'),
    ("plugins.py", 'module = __import__(f"plugins.{name}")\n'),
    ("plugins.py", 'factory = globals()["make_" + kind]\n'),
    ("orders.js", 'const mod = require("./handlers/" + kind);\n'),
    ("orders.ts", "const mod = await import(`./handlers/${kind}`);\n"),
    ("orders.ts", 'this["handle" + kind](order);\n'),
    ("orders.rb", 'send("handle_#{kind}", order)\n'),
    ("Orders.java", 'Class.forName("handlers." + kind);\n'),
    ("orders.go", 'value.MethodByName("Handle" + kind)\n'),
]

LITERAL_SAMPLES = [
    ("orders.py", PY_LITERAL),
    ("orders.py", "handler = getattr(self, attribute_name)\n"),
    ("orders.py", 'total = "order " + str(order_id)\n'),
    ("plugins.py", 'module = importlib.import_module("plugins.refund")\n'),
    ("orders.js", 'const fs = require("fs");\n'),
    ("orders.ts", 'const mod = await import("./handlers/refund");\n'),
    ("orders.ts", "const first = items[index + 1];\n"),
    ("orders.rb", "send(:handle_refund, order)\n"),
    ("notes.md", PY_ASSEMBLED),
]


def _run_hook(hook_name: str, tool_input: dict) -> subprocess.CompletedProcess:
    env = {**os.environ, "WORKTREE_GUARD_DISABLE": "1"}
    return subprocess.run(
        ["python3", str(HOOKS_DIR / hook_name)],
        input=json.dumps({"tool_input": tool_input}),
        capture_output=True,
        text=True,
        env=env,
    )


@pytest.mark.parametrize("file_path,content", ASSEMBLED_SAMPLES)
def test_check_with_assembled_name_exits_2(file_path: str, content: str):
    with pytest.raises(SystemExit) as blocked:
        dynamic_name_guard.check(file_path, "", content)
    assert blocked.value.code == 2


@pytest.mark.parametrize("file_path,content", LITERAL_SAMPLES)
def test_check_with_literal_name_does_not_block(file_path: str, content: str):
    assert dynamic_name_guard.check(file_path, "", content) is None


def test_check_with_test_file_does_not_block():
    outcome = dynamic_name_guard.check("test_orders.py", "", PY_ASSEMBLED)
    assert outcome is None


def test_check_with_assembled_name_already_present_does_not_block():
    edited = PY_ASSEMBLED + "total = 1\n"
    outcome = dynamic_name_guard.check("orders.py", PY_ASSEMBLED, edited)
    assert outcome is None


def test_check_with_second_assembled_name_added_exits_2():
    with pytest.raises(SystemExit) as blocked:
        dynamic_name_guard.check("orders.py", PY_ASSEMBLED, PY_ASSEMBLED * 2)
    assert blocked.value.code == 2


def test_check_with_guard_disabled_does_not_block(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("DYNAMIC_NAME_GUARD_DISABLE", "1")
    assert dynamic_name_guard.check("orders.py", "", PY_ASSEMBLED) is None


def test_pre_write_with_assembled_name_exits_2():
    probe = HOOKS_DIR / "_dynamic_name_probe.py"
    tool_input = {"file_path": str(probe), "content": PY_ASSEMBLED}
    result = _run_hook("pre-write.py", tool_input)
    assert result.returncode == 2, result.stderr
    assert "assembled at runtime" in result.stderr


def test_pre_edit_with_assembled_name_added_exits_2():
    target = HOOKS_DIR / "hook_lib.py"
    tool_input = {
        "file_path": str(target),
        "old_string": PY_LITERAL,
        "new_string": PY_ASSEMBLED,
    }
    result = _run_hook("pre-edit.py", tool_input)
    assert result.returncode == 2, result.stderr
    assert "assembled at runtime" in result.stderr
