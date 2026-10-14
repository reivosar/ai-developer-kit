"""Tests for doc_comment_guard: public code carries a doc comment that fits it."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import doc_comment_guard  # noqa: E402
from doc_comment_guard import find_violations  # noqa: E402

HOOKS_DIR = Path(__file__).parent
# The kit's own hooks are held to the rule one module at a time, so a failure
# names the module. A new hook module fails the list test until it is added.
HOOK_MODULES = [
    "anomaly_guard.py", "audit_log.py", "bash_guard.py", "commit_guard.py",
    "content_guard.py", "coverage_guard.py", "coverage_runners.py", "cp_guard.py",
    "doc_comment_guard.py", "doc_comments.py", "doc_length_guard.py",
    "dynamic_name_guard.py", "env_file_guard.py", "fail_closed.py",
    "function_definitions.py",
    "function_length_guard.py", "git_guard.py", "hook_lib.py", "mcp_guard.py",
    "memory_guard.py", "post-tool.py", "pre-bash.py", "pre-edit.py",
    "pre-mcp.py", "pre-write.py", "prompt_injection_guard.py",
    "rate_limiter.py", "reference_notice.py", "run-hook.py",
    "static_analysis_guard.py",
    "tdd_guard.py", "template_guard.py", "testing_guard.py",
    "user-prompt-submit.py",
    "worktree_guard.py",
]
PY_DOCUMENTED = (
    "def apply_discount(total, rate):\n"
    '    """Return the total after the discount."""\n'
    "    return total - rate\n"
)
PY_UNDOCUMENTED = "def apply_fee(total, fee):\n    return total + fee\n"
PY_ARGS = '''
def apply_discount(total, rate, *fees, **options):
    """Return the total after the discount.

    Args:
        total (int): The amount before the discount.
            Continued: on a second line.
        rate: The discount.
        *fees: Extra fees.
        **options: Rounding options.

    Returns:
        int: The discounted total.
    """
    return total - rate
'''
JAVA_METHOD = '''
    /**
     * Returns the total.
     *
     * @param <T> the line type
     * @param total the amount
     * @param rate the tax rate
     */
    public <T> int applyTax(int total, int rate) {
        return total + rate;
    }
'''
TS_FUNCTION = '''
/**
 * Returns the discounted total.
 * @param {number} total - The amount.
 * @param {number} [rate=0] - The discount.
 */
export function applyDiscount(total: number, rate = 0): number {
  return total - rate;
}
'''
TS_DESTRUCTURED = '''
/**
 * Renders the total.
 * @param props.total - The amount.
 */
export function render({ total }: Props): string {
  return String(total);
}
'''
GO_FUNCTION = (
    "// ApplyDiscount returns the discounted total.\n"
    "func ApplyDiscount(total int) int {\n\treturn total\n}\n"
)
GO_TYPE = "// An Order is one customer order.\ntype Order struct{}\n"
RUST_FUNCTION = (
    "/// Adds the fee to the total.\n"
    "#[inline]\n"
    "pub fn apply_fee(total: u32, fee: u32) -> u32 {\n    total + fee\n}\n"
)


def _blocked_reasons(capsys: pytest.CaptureFixture, check, *arguments) -> str:
    with pytest.raises(SystemExit) as blocked:
        check(*arguments)
    assert blocked.value.code == 2
    return capsys.readouterr().err


@pytest.mark.parametrize(
    "code, file_name",
    [
        (PY_DOCUMENTED, "orders.py"),
        (PY_ARGS, "orders.py"),
        (JAVA_METHOD, "Order.java"),
        (TS_FUNCTION, "order.ts"),
        (TS_DESTRUCTURED, "order.ts"),
        (GO_FUNCTION, "orders.go"),
        (GO_TYPE, "orders.go"),
        (RUST_FUNCTION, "orders.rs"),
        (PY_UNDOCUMENTED, "orders.rb"),
    ],
)
def test_find_violations_with_fitting_doc_comment_returns_nothing(
    code: str, file_name: str
):
    assert find_violations(code, file_name) == []


def test_find_violations_with_undocumented_python_function_reports_it():
    assert find_violations(PY_UNDOCUMENTED, "orders.py") == [
        "apply_fee: no doc comment"
    ]


@pytest.mark.parametrize(
    "code, file_name, name",
    [
        ('def apply_fee(total):\n    """   """\n', "orders.py", "apply_fee"),
        ("/** */\nexport function applyFee(total) {}\n", "order.js", "applyFee"),
        ("/**\n *\n */\npublic int applyFee(int total) {}\n", "Order.java", "applyFee"),
        ("func ApplyFee(total int) int {}\n", "orders.go", "ApplyFee"),
        ("fun applyFee(total: Int): Int = total\n", "Order.kt", "applyFee"),
        ("pub fn apply_fee(total: u32) -> u32 { total }\n", "orders.rs", "apply_fee"),
    ],
)
def test_find_violations_with_missing_or_empty_doc_comment_reports_it(
    code: str, file_name: str, name: str
):
    assert find_violations(code, file_name) == [f"{name}: no doc comment"]


def test_find_violations_with_python_args_naming_a_removed_parameter_reports_it():
    code = PY_ARGS.replace("def apply_discount(total, rate,", "def apply_discount(total,")
    assert find_violations(code, "orders.py") == [
        "apply_discount: doc comment names parameter 'rate',"
        " which the signature does not have"
    ]


def test_find_violations_with_python_args_omitting_a_parameter_reports_it():
    code = PY_ARGS.replace("        rate: The discount.\n", "")
    assert find_violations(code, "orders.py") == [
        "apply_discount: doc comment lists parameters but omits 'rate'"
    ]


def test_find_violations_with_java_tags_out_of_step_reports_both_directions():
    code = JAVA_METHOD.replace("int total, int rate", "int total, int fee")
    assert find_violations(code, "Order.java") == [
        "applyTax: doc comment names parameter 'rate',"
        " which the signature does not have",
        "applyTax: doc comment lists parameters but omits 'fee'",
    ]


def test_find_violations_with_typescript_tag_for_renamed_parameter_reports_it():
    code = TS_FUNCTION.replace("total: number, rate = 0", "amount: number, rate = 0")
    assert find_violations(code, "order.ts") == [
        "applyDiscount: doc comment names parameter 'total',"
        " which the signature does not have",
        "applyDiscount: doc comment lists parameters but omits 'amount'",
    ]


def test_find_violations_with_kotlin_tag_for_removed_parameter_reports_it():
    code = (
        "/**\n * Returns the total.\n * @param rate the tax rate\n */\n"
        "fun total(): Int = 0\n"
    )
    assert find_violations(code, "Order.kt") == [
        "total: doc comment names parameter 'rate',"
        " which the signature does not have"
    ]


@pytest.mark.parametrize(
    "comment", ["// Returns the discounted total.", "// applyDiscount returns it."]
)
def test_find_violations_with_go_comment_not_starting_with_name_reports_it(
    comment: str,
):
    code = f"{comment}\nfunc ApplyDiscount(total int) int {{\n\treturn total\n}}\n"
    assert find_violations(code, "orders.go") == [
        "ApplyDiscount: doc comment must start with 'ApplyDiscount'"
    ]


def test_check_write_with_undocumented_function_exits_2(
    capsys: pytest.CaptureFixture,
):
    reasons = _blocked_reasons(
        capsys, doc_comment_guard.check_write, "orders.py", PY_UNDOCUMENTED
    )
    assert "apply_fee: no doc comment" in reasons
    assert "code-style.md" in reasons


@pytest.mark.parametrize("file_name", ["orders.py", "src/test_orders.py"])
def test_check_write_with_documented_or_test_file_does_not_block(file_name: str):
    code = PY_DOCUMENTED if file_name == "orders.py" else PY_UNDOCUMENTED
    assert doc_comment_guard.check_write(file_name, code) is None


def test_check_write_with_guard_disabled_does_not_block(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("DOC_COMMENT_GUARD_DISABLE", "1")
    assert doc_comment_guard.check_write("orders.py", PY_UNDOCUMENTED) is None


def test_check_edit_adding_undocumented_function_exits_2(
    tmp_path: Path, capsys: pytest.CaptureFixture
):
    target = tmp_path / "orders.py"
    target.write_text(PY_DOCUMENTED)
    reasons = _blocked_reasons(
        capsys, doc_comment_guard.check_edit, str(target),
        PY_DOCUMENTED, PY_DOCUMENTED + "\n\n" + PY_UNDOCUMENTED,
    )
    assert "apply_fee: no doc comment" in reasons


def test_check_edit_changing_body_of_undocumented_function_does_not_block(
    tmp_path: Path,
):
    target = tmp_path / "orders.py"
    target.write_text(PY_UNDOCUMENTED)
    edited = doc_comment_guard.check_edit(
        str(target), "return total + fee", "return fee + total"
    )
    assert edited is None


def test_check_edit_adding_second_undocumented_function_of_same_name_exits_2(
    tmp_path: Path, capsys: pytest.CaptureFixture
):
    target = tmp_path / "orders.py"
    target.write_text(PY_UNDOCUMENTED)
    reasons = _blocked_reasons(
        capsys, doc_comment_guard.check_edit, str(target),
        PY_UNDOCUMENTED, PY_UNDOCUMENTED + "\n\n" + PY_UNDOCUMENTED,
    )
    assert "apply_fee: no doc comment" in reasons


def test_check_edit_renaming_documented_parameter_exits_2(
    tmp_path: Path, capsys: pytest.CaptureFixture
):
    target = tmp_path / "orders.py"
    target.write_text(PY_ARGS)
    reasons = _blocked_reasons(
        capsys, doc_comment_guard.check_edit, str(target),
        "def apply_discount(total, rate,", "def apply_discount(total, percent,",
    )
    assert "omits 'percent'" in reasons


def test_check_edit_of_file_that_does_not_exist_does_not_block(tmp_path: Path):
    target = tmp_path / "orders.py"
    assert doc_comment_guard.check_edit(str(target), "", PY_UNDOCUMENTED) is None


@pytest.mark.parametrize("module_name", HOOK_MODULES)
def test_find_violations_in_hook_module_returns_nothing(module_name: str):
    module = HOOKS_DIR / module_name
    assert find_violations(module.read_text(), module_name) == []


def test_hook_module_list_names_every_hook_module():
    modules = [
        path.name for path in HOOKS_DIR.glob("*.py")
        if not path.name.startswith("test_") and path.name != "conftest.py"
    ]
    assert HOOK_MODULES == sorted(modules)


def _run_hook(hook_name: str, tool_input: dict) -> subprocess.CompletedProcess:
    env = {
        **os.environ,
        "WORKTREE_GUARD_DISABLE": "1",
        "ANOMALY_PATH_ESCAPE_DISABLE": "1",
        "TDD_GUARD_DISABLE": "1",
    }
    return subprocess.run(
        ["python3", str(HOOKS_DIR / hook_name)],
        input=json.dumps({"tool_input": tool_input}),
        capture_output=True, text=True, env=env,
    )


def test_pre_write_with_undocumented_function_exits_2():
    probe = HOOKS_DIR / "doc_comment_probe.py"
    tool_input = {"file_path": str(probe), "content": PY_UNDOCUMENTED}
    result = _run_hook("pre-write.py", tool_input)
    assert result.returncode == 2, result.stderr
    assert "apply_fee: no doc comment" in result.stderr


def test_pre_edit_adding_undocumented_function_exits_2(tmp_path: Path):
    target = tmp_path / "orders.py"
    target.write_text(PY_DOCUMENTED)
    tool_input = {
        "file_path": str(target),
        "old_string": PY_DOCUMENTED,
        "new_string": PY_DOCUMENTED + "\n\n" + PY_UNDOCUMENTED,
    }
    result = _run_hook("pre-edit.py", tool_input)
    assert result.returncode == 2, result.stderr
    assert "apply_fee: no doc comment" in result.stderr
