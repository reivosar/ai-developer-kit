"""Tests for testing_guard: a test must satisfy the decidable test rules."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import testing_guard  # noqa: E402

HOOKS_DIR = Path(__file__).parent
NAME = "test_cancel_order_twice_raises"


def _python_test(body: str, name: str = NAME) -> str:
    return f"def {name}():\n{body}\n"


PY_GOOD = _python_test("    assert cancel_order(1) == 1")
PY_NO_ASSERT = _python_test("    cancel_order(1)")
JS_GOOD = 'it("cancels once", () => {\n  expect(cancel(1)).toBe(1);\n});\n'
JS_NO_ASSERT = 'it("cancels once", () => {\n  cancel(1);\n});\n'
GO_GOOD = "func TestCancel(t *testing.T) {\n\tt.Errorf(\"failed\")\n}\n"
GO_NO_ASSERT = "func TestCancel(t *testing.T) {\n\tCancel(1)\n}\n"

VIOLATIONS = [
    (PY_NO_ASSERT, "test_orders.py", f"{NAME}: no assertion"),
    (
        _python_test("    cancel_order(1)\n    assert True"),
        "test_orders.py",
        f"{NAME}: assertion that is always true",
    ),
    (
        _python_test("    assert 1 == 1"),
        "test_orders.py",
        f"{NAME}: assertion that is always true",
    ),
    (
        _python_test("    time.sleep(1)\n    assert cancel_order(1) == 1"),
        "test_orders.py",
        f"{NAME}: sleep in a test",
    ),
    (
        _python_test("    assert render(order) == snapshot"),
        "test_orders.py",
        f"{NAME}: snapshot test",
    ),
    (
        _python_test("    assert cancel_order(1) == 1", "test_cancel"),
        "test_orders.py",
        "test_cancel: name needs"
        " test_<function>_<scenario>_<expected_outcome>",
    ),
    (
        PY_GOOD + 'if __name__ == "__main__":\n    run_all()\n',
        "test_orders.py",
        "module: __main__ runner block",
    ),
    (
        PY_GOOD + "def check(ok):\n    global passed\n    passed += 1\n",
        "test_orders.py",
        "module: pass/fail counters",
    ),
    (JS_NO_ASSERT, "orders.test.ts", "cancels once: no assertion"),
    (
        'it("cancels once", () => {\n  expect(true).toBe(true);\n});\n',
        "orders.test.ts",
        "cancels once: assertion that is always true",
    ),
    (
        'test("cancels once", async () => {\n  await new Promise((done) =>'
        " setTimeout(done, 50));\n  expect(cancel(1)).toBe(1);\n});\n",
        "orders.test.js",
        "cancels once: sleep in a test",
    ),
    (
        'it("renders", () => {\n  expect(render()).toMatchSnapshot();\n});\n',
        "orders.test.tsx",
        "renders: snapshot test",
    ),
    (GO_NO_ASSERT, "orders_test.go", "TestCancel: no assertion"),
    (
        "func TestCancel(t *testing.T) {\n\ttime.Sleep(time.Second)\n"
        "\tt.Fatal(\"failed\")\n}\n",
        "orders_test.go",
        "TestCancel: sleep in a test",
    ),
]

VALID = [
    (PY_GOOD, "test_orders.py"),
    (
        _python_test(
            "    with pytest.raises(ValueError):\n        cancel_order(1)"
        ),
        "test_orders.py",
    ),
    (_python_test("    mailer.send.assert_called_once()"), "test_orders.py"),
    (_python_test("    _assert_cancelled(cancel_order(1))"), "test_orders.py"),
    (JS_GOOD, "orders.test.ts"),
    (GO_GOOD, "orders_test.go"),
    (PY_NO_ASSERT, "orders_test.rb"),
]


def _run_hook(hook_name: str, tool_input: dict) -> subprocess.CompletedProcess:
    env = {
        **os.environ,
        "WORKTREE_GUARD_DISABLE": "1",
        "ANOMALY_PATH_ESCAPE_DISABLE": "1",
    }
    return subprocess.run(
        ["python3", str(HOOKS_DIR / hook_name)],
        input=json.dumps({"tool_input": tool_input}),
        capture_output=True,
        text=True,
        env=env,
    )


@pytest.mark.parametrize("code,file_path,expected", VIOLATIONS)
def test_find_violations_with_broken_test_reports_violation(
    code: str, file_path: str, expected: str
):
    assert testing_guard.find_violations(code, file_path) == {expected}


@pytest.mark.parametrize("code,file_path", VALID)
def test_find_violations_with_valid_test_reports_nothing(
    code: str, file_path: str
):
    assert testing_guard.find_violations(code, file_path) == set()


def test_find_violations_with_two_tests_reports_only_broken_test():
    second = _python_test("    refund_order(1)", "test_refund_order_once_pays")
    violations = testing_guard.find_violations(
        PY_GOOD + "\n" + second, "test_orders.py"
    )
    assert violations == {"test_refund_order_once_pays: no assertion"}


def test_check_write_with_broken_test_exits_2():
    with pytest.raises(SystemExit) as blocked:
        testing_guard.check_write("test_orders.py", PY_NO_ASSERT)
    assert blocked.value.code == 2


def test_check_write_with_valid_test_returns_without_blocking():
    assert testing_guard.check_write("test_orders.py", PY_GOOD) is None


def test_check_write_with_implementation_file_returns_without_blocking():
    assert testing_guard.check_write("orders.py", PY_NO_ASSERT) is None


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
