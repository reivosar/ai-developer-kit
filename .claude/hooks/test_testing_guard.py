"""Tests for testing_guard: a test must satisfy the decidable test rules."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import testing_guard  # noqa: E402

NAME = "test_cancel_order_twice_raises"


def _python_test(body: str, name: str = NAME) -> str:
    return f"def {name}():\n{body}\n"


PY_GOOD = _python_test("    assert cancel_order(1) == 1")
PY_NO_ASSERT = _python_test("    cancel_order(1)")
JS_GOOD = 'it("cancels once", () => {\n  expect(cancel(1)).toBe(1);\n});\n'
JS_NO_ASSERT = 'it("cancels once", () => {\n  cancel(1);\n});\n'
GO_GOOD = "func TestCancel(t *testing.T) {\n\tt.Errorf(\"failed\")\n}\n"
GO_NO_ASSERT = "func TestCancel(t *testing.T) {\n\tCancel(1)\n}\n"
RUST_IMPLEMENTATION = "pub fn cancel(id: u32) -> u32 {\n    sleep(id);\n    id\n}\n\n"


def _rust_test(body: str, attributes: str = "#[test]") -> str:
    test = f"    {attributes}\n    fn cancels_once() {{\n    {body}\n    }}\n"
    return f"{RUST_IMPLEMENTATION}#[cfg(test)]\nmod tests {{\n{test}}}\n"


RUST_GOOD = _rust_test("    assert_eq!(cancel(1), 1);")
RUST_NO_ASSERT = _rust_test("    cancel(1);")

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
    (RUST_NO_ASSERT, "src/orders.rs", "cancels_once: no assertion"),
    (
        _rust_test("    assert!(true);"),
        "tests/orders.rs",
        "cancels_once: assertion that is always true",
    ),
    (
        _rust_test("    assert_eq!(1, 1);"),
        "tests/orders.rs",
        "cancels_once: assertion that is always true",
    ),
    (
        _rust_test(
            "    std::thread::sleep(Duration::from_secs(1));\n"
            "    assert_eq!(cancel(1), 1);"
        ),
        "src/orders.rs",
        "cancels_once: sleep in a test",
    ),
    (
        _rust_test("    insta::assert_snapshot!(render());"),
        "src/orders.rs",
        "cancels_once: snapshot test",
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
    (RUST_GOOD, "src/orders.rs"),
    (_rust_test("    cancel(1);", "#[test]\n    #[should_panic]"), "src/orders.rs"),
    (
        _rust_test("    assert!(fetch(1).await.is_ok());", "#[tokio::test]"),
        "tests/orders.rs",
    ),
    (RUST_IMPLEMENTATION, "src/orders.rs"),
    (PY_NO_ASSERT, "orders_test.rb"),
]


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
