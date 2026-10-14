"""Tests for function_length_guard: a function body stays within the limit."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import function_length_guard  # noqa: E402
from function_length_guard import find_violations, function_lengths  # noqa: E402

HOOKS_DIR = Path(__file__).parent
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


def _blocked_reasons(capsys: pytest.CaptureFixture, check, *arguments) -> str:
    with pytest.raises(SystemExit) as blocked:
        check(*arguments)
    assert blocked.value.code == 2
    return capsys.readouterr().err


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


def test_find_violations_at_the_limit_returns_nothing():
    assert find_violations(_python("apply_discount", 20), "orders.py") == []


def test_find_violations_one_line_over_the_limit_reports_the_function():
    assert find_violations(_python("apply_discount", 21), "orders.py") == [
        "apply_discount: body is 21 lines; the limit is 20"
    ]


def test_check_write_with_long_function_exits_2(capsys: pytest.CaptureFixture):
    reasons = _blocked_reasons(
        capsys, function_length_guard.check_write, "orders.py",
        _python("apply_discount", 21),
    )
    assert "apply_discount: body is 21 lines; the limit is 20" in reasons
    assert "code-style.md" in reasons


@pytest.mark.parametrize(
    "file_name, lines", [("orders.py", 20), ("src/test_orders.py", 30)]
)
def test_check_write_within_limit_or_in_test_file_does_not_block(
    file_name: str, lines: int
):
    code = _python("apply_discount", lines)
    assert function_length_guard.check_write(file_name, code) is None


def test_check_write_with_guard_disabled_does_not_block(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("FUNCTION_LENGTH_GUARD_DISABLE", "1")
    code = _python("apply_discount", 21)
    assert function_length_guard.check_write("orders.py", code) is None


def test_check_edit_adding_long_function_exits_2(
    tmp_path: Path, capsys: pytest.CaptureFixture
):
    target = tmp_path / "orders.py"
    target.write_text(_python("apply_fee", 5))
    added = _python("apply_fee", 5) + "\n\n" + _python("apply_discount", 21)
    reasons = _blocked_reasons(
        capsys, function_length_guard.check_edit, str(target),
        _python("apply_fee", 5), added,
    )
    assert "apply_discount: body is 21 lines" in reasons


@pytest.mark.parametrize(
    "old_line, new_line",
    [
        ("    total += 3\n", "    total += 300\n"),
        ("    total += 3\n", ""),
    ],
)
def test_check_edit_keeping_or_shortening_long_function_does_not_block(
    tmp_path: Path, old_line: str, new_line: str
):
    target = tmp_path / "orders.py"
    target.write_text(_python("apply_discount", 30))
    edited = function_length_guard.check_edit(str(target), old_line, new_line)
    assert edited is None


def test_check_edit_lengthening_long_function_exits_2(
    tmp_path: Path, capsys: pytest.CaptureFixture
):
    target = tmp_path / "orders.py"
    target.write_text(_python("apply_discount", 30))
    reasons = _blocked_reasons(
        capsys, function_length_guard.check_edit, str(target),
        "    total += 3\n", "    total += 3\n    total += 300\n",
    )
    assert "apply_discount: body is 31 lines; the limit is 20" in reasons


def test_check_edit_of_file_that_does_not_exist_does_not_block(tmp_path: Path):
    target = tmp_path / "orders.py"
    code = _python("apply_discount", 21)
    assert function_length_guard.check_edit(str(target), "", code) is None


def test_find_violations_in_every_hook_module_returns_nothing():
    modules = [
        path for path in sorted(HOOKS_DIR.glob("*.py"))
        if not path.name.startswith("test_")
    ]
    found = {
        path.name: find_violations(path.read_text(), path.name) for path in modules
    }
    assert {name: listed for name, listed in found.items() if listed} == {}


def _run_hook(hook_name: str, tool_input: dict) -> subprocess.CompletedProcess:
    env = {
        **os.environ,
        "WORKTREE_GUARD_DISABLE": "1",
        "ANOMALY_PATH_ESCAPE_DISABLE": "1",
        "TDD_GUARD_DISABLE": "1",
    }
    return subprocess.run(
        [sys.executable, str(HOOKS_DIR / hook_name)],
        input=json.dumps({"tool_input": tool_input}),
        capture_output=True, text=True, env=env,
    )


def test_pre_write_with_long_function_exits_2():
    probe = HOOKS_DIR / "function_length_probe.py"
    content = _python("apply_discount", 21, DOCSTRING)
    result = _run_hook("pre-write.py", {"file_path": str(probe), "content": content})
    assert result.returncode == 2, result.stderr
    assert "apply_discount: body is 21 lines" in result.stderr


def test_pre_edit_lengthening_function_past_limit_exits_2(tmp_path: Path):
    target = tmp_path / "orders.py"
    target.write_text(_python("apply_discount", 20, DOCSTRING))
    tool_input = {
        "file_path": str(target),
        "old_string": "    total += 3\n",
        "new_string": "    total += 3\n    total += 300\n",
    }
    result = _run_hook("pre-edit.py", tool_input)
    assert result.returncode == 2, result.stderr
    assert "apply_discount: body is 21 lines" in result.stderr
