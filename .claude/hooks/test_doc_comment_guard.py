"""Tests for doc_comment_guard: public code carries a doc comment that fits it."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from doc_comment_guard import find_violations  # noqa: E402

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
