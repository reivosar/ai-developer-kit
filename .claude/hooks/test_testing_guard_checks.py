"""Tests for testing_guard's Write and Edit checks, also through the hooks."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import testing_guard  # noqa: E402

HOOKS_DIR = Path(__file__).parent
PY_GOOD = "def test_cancel_order_twice_raises():\n    assert cancel_order(1) == 1\n"
PY_NO_ASSERT = "def test_cancel_order_twice_raises():\n    cancel_order(1)\n"
RUST_IMPLEMENTATION = "pub fn cancel(id: u32) -> u32 {\n    sleep(id);\n    id\n}\n\n"
RUST_NO_ASSERT = (
    f"{RUST_IMPLEMENTATION}#[cfg(test)]\nmod tests {{\n"
    "    #[test]\n    fn cancels_once() {\n        cancel(1);\n    }\n}\n"
)


def _run_hook(hook_name: str, tool_input: dict) -> subprocess.CompletedProcess:
    env = {
        **os.environ,
        "WORKTREE_GUARD_DISABLE": "1",
        "ANOMALY_PATH_ESCAPE_DISABLE": "1",
    }
    return subprocess.run(
        [sys.executable, str(HOOKS_DIR / hook_name)],
        input=json.dumps({"tool_input": tool_input}),
        capture_output=True, text=True, env=env,
    )


def test_check_write_with_broken_test_exits_2():
    with pytest.raises(SystemExit) as blocked:
        testing_guard.check_write("test_orders.py", PY_NO_ASSERT)
    assert blocked.value.code == 2


@pytest.mark.parametrize(
    "file_path, code", [("test_orders.py", PY_GOOD), ("orders.py", PY_NO_ASSERT)]
)
def test_check_write_with_valid_test_or_implementation_does_not_block(
    file_path: str, code: str
):
    assert testing_guard.check_write(file_path, code) is None


def test_check_write_with_guard_disabled_returns_without_blocking(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("TESTING_GUARD_DISABLE", "1")
    assert testing_guard.check_write("test_orders.py", PY_NO_ASSERT) is None


def test_check_edit_adding_broken_test_exits_2(tmp_path: Path):
    target = tmp_path / "test_orders.py"
    target.write_text(PY_GOOD)
    with pytest.raises(SystemExit) as blocked:
        testing_guard.check_edit(str(target), PY_GOOD, PY_GOOD + PY_NO_ASSERT)
    assert blocked.value.code == 2


def test_check_edit_in_file_with_existing_violation_does_not_block(
    tmp_path: Path,
):
    target = tmp_path / "test_orders.py"
    target.write_text(PY_NO_ASSERT + "\nLIMIT = 1\n")
    edited = testing_guard.check_edit(str(target), "LIMIT = 1", "LIMIT = 2")
    assert edited is None


def test_check_edit_removing_violation_does_not_block(tmp_path: Path):
    target = tmp_path / "test_orders.py"
    target.write_text(PY_NO_ASSERT)
    assert testing_guard.check_edit(str(target), PY_NO_ASSERT, PY_GOOD) is None


def test_check_edit_with_missing_file_does_not_block(tmp_path: Path):
    absent = str(tmp_path / "test_orders.py")
    assert testing_guard.check_edit(absent, "", PY_NO_ASSERT) is None


def test_pre_write_with_broken_test_exits_2():
    probe = HOOKS_DIR / "test_guard_probe.py"
    tool_input = {"file_path": str(probe), "content": PY_NO_ASSERT}
    result = _run_hook("pre-write.py", tool_input)
    assert result.returncode == 2, result.stderr
    assert "no assertion" in result.stderr


def test_pre_edit_adding_broken_test_exits_2(tmp_path: Path):
    target = tmp_path / "test_orders.py"
    target.write_text(PY_GOOD)
    tool_input = {
        "file_path": str(target),
        "old_string": PY_GOOD,
        "new_string": PY_GOOD + PY_NO_ASSERT,
    }
    result = _run_hook("pre-edit.py", tool_input)
    assert result.returncode == 2, result.stderr
    assert "no assertion" in result.stderr


def test_check_write_with_broken_test_inside_rust_source_file_exits_2(
    capsys: pytest.CaptureFixture,
):
    with pytest.raises(SystemExit) as blocked:
        testing_guard.check_write("src/orders.rs", RUST_NO_ASSERT)
    assert blocked.value.code == 2
    assert "cancels_once: no assertion" in capsys.readouterr().err


def test_check_write_with_rust_source_file_without_tests_does_not_block():
    assert testing_guard.check_write("src/orders.rs", RUST_IMPLEMENTATION) is None
