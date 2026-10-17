"""Tests for function_lengths: the body length of each function, per language."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from function_lengths import function_lengths  # noqa: E402

DOCSTRING = '    """Return the total."""\n\n    # Start from nothing.\n'


def _python(name: str, lines: int, heading: str = "") -> str:
    steps = "".join(f"    total += {step}\n" for step in range(lines - 2))
    return f"def {name}():\n{heading}    total = 0\n{steps}    return total\n"


def _braces(opening: str, lines: int, indent: str = "") -> str:
    steps = "".join(f"{indent}  total += {step};\n" for step in range(lines))
    return f"{indent}{opening} {{\n{steps}{indent}}}\n"


BRACE_FUNCTIONS = [
    ("orders.go", "func ApplyDiscount(total int) (int, error)", "ApplyDiscount"),
    ("orders.go", "func (o *Order) Total(rate int) int", "Total"),
    ("Order.kt", "suspend fun applyDiscount(total: Int): Int", "applyDiscount"),
    ("Order.java", "public static int applyDiscount(int total)", "applyDiscount"),
    ("Order.java", "Order(String id) throws IOException", "Order"),
    ("order.ts", "export async function applyDiscount(total: number)", "applyDiscount"),
    ("order.ts", "const applyDiscount = (total: number): number =>", "applyDiscount"),
    ("order.ts", "async fetchOrder(id: string): Promise<Order>", "fetchOrder"),
    ("order.js", "static create(lines)", "create"),
    (
        "orders.rs",
        "pub fn apply_discount(total: u32) -> Result<u32, Error>",
        "apply_discount",
    ),
    (
        "orders.rs",
        "pub async fn fetch<T: Into<String>>(id: T) -> impl Iterator<Item = u32>",
        "fetch",
    ),
    ("orders.rs", "fn label<'a>(&'a self, name: &'a str) -> &'a str", "label"),
    ('orders.rs', 'pub unsafe extern "C" fn total(count: u32) -> u32', "total"),
]
NOT_FUNCTIONS = [
    ("order.js", "if (ready)"),
    ("order.js", "for (const line of lines)"),
    ("order.js", "it('adds the lines', () =>"),
    ("Order.java", "return new Order(id)"),
    ("Order.java", "synchronized (lock)"),
    ("orders.go", "var totals = map[string]int"),
]


def test_function_lengths_in_python_counts_body_lines():
    assert function_lengths(_python("apply_discount", 20), "orders.py") == [
        ("apply_discount", 20)
    ]


def test_function_lengths_in_python_leaves_out_docstring_blank_and_comment():
    code = _python("apply_discount", 20, DOCSTRING)
    assert function_lengths(code, "orders.py") == [("apply_discount", 20)]


def test_function_lengths_in_python_measures_method_and_nested_function():
    code = (
        "class Order:\n"
        "    def total(self):\n"
        "        def add(left, right):\n"
        "            return left + right\n"
        "        return add(1, 2)\n"
    )
    assert function_lengths(code, "orders.py") == [("total", 3), ("add", 1)]


def test_function_lengths_in_python_with_syntax_error_returns_nothing():
    assert function_lengths("def broken(:\n", "orders.py") == []


@pytest.mark.parametrize("file_name, opening, name", BRACE_FUNCTIONS)
def test_function_lengths_in_brace_language_counts_body_lines(
    file_name: str, opening: str, name: str
):
    code = _braces(opening, 21, indent="  ")
    assert function_lengths(code, file_name) == [(name, 21)]


def test_function_lengths_in_brace_language_leaves_out_comments_and_strings():
    code = (
        "func ApplyDiscount(total int) int {\n"
        "\t// A closing brace in a comment: }\n"
        "\n"
        "\t/* A block comment\n"
        "\t   over two lines { */\n"
        "\tlabel := \"}{\"\n"
        "\treturn total\n"
        "}\n"
    )
    assert function_lengths(code, "orders.go") == [("ApplyDiscount", 2)]


def test_function_lengths_in_rust_reads_lifetimes_and_char_literals():
    code = (
        "fn label<'a>(name: &'a str) -> &'a str {\n"
        "    let open = '{';\n"
        "    let quote = '\\'';\n"
        "    let text = \"}\";\n"
        "    name\n"
        "}\n"
    )
    assert function_lengths(code, "orders.rs") == [("label", 4)]


@pytest.mark.parametrize("file_name, opening", NOT_FUNCTIONS)
def test_function_lengths_with_block_that_is_not_a_function_returns_nothing(
    file_name: str, opening: str
):
    assert function_lengths(_braces(opening, 25, indent="  "), file_name) == []


@pytest.mark.parametrize(
    "code, file_name",
    [
        ("fun total(): Int = lines.sum()\n", "Order.kt"),
        ("  total(rate: number): number;\n", "order.ts"),
        ("  abstract int total(int rate);\n", "Order.java"),
        ("    fn next(&mut self) -> Option<Order>;\n", "orders.rs"),
        (_python("apply_discount", 30), "orders.rb"),
    ],
)
def test_function_lengths_with_no_measurable_body_returns_nothing(
    code: str, file_name: str
):
    assert function_lengths(code, file_name) == []
