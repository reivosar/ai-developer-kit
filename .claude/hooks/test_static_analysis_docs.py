"""Tests for static-analysis.sh: public code without fitting doc comments fails lint.

Python is linted by ruff's pydocstyle (D) and pydoclint (DOC) rules with the
kit's lint-config/ruff-docs.toml. The real-tool tests need ruff, which the
script installs when it is missing.
"""
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent / "static-analysis.sh"
RUFF_DOCS = (
    f"ruff check --config {SCRIPT.parent / 'lint-config' / 'ruff-docs.toml'}"
    " --output-format concise --no-cache"
)
MODULE_DOC = '"""Orders."""\n\n\n'
DOCUMENTED = MODULE_DOC + (
    "def refund(order: dict, rate: float) -> float:\n"
    '    """Refund an order.\n\n    Paid orders are refunded at the rate.\n\n'
    "    Args:\n        order: the order to refund.\n"
    "        rate: the share of the total paid back.\n\n"
    "    Returns:\n        The amount refunded.\n\n"
    "    Raises:\n        ValueError: the order has no total.\n"
    '    """\n'
    '    if "total" not in order:\n        raise ValueError("no total")\n'
    '    return order["total"] * rate\n'
)


def _run(source: Path) -> subprocess.CompletedProcess:
    return subprocess.run([str(SCRIPT), str(source)], capture_output=True, text=True)


def test_static_analysis_with_python_file_runs_ruff_doc_rules(tmp_path: Path, tool_stubs):
    module = tmp_path / "orders.py"
    module.write_text(MODULE_DOC)
    for name in ["flake8", "pylint", "ruff"]:
        tool_stubs.add(name)
    result = tool_stubs.run_script(SCRIPT, str(module))
    assert result.returncode == 0, result.stderr
    assert f"{RUFF_DOCS} {module}" in tool_stubs.calls()


@pytest.mark.parametrize("code, rule", [
    (
        MODULE_DOC + "def refund(order: dict) -> int:\n    return 1\n",
        "undocumented-public-function",
    ),
    (
        MODULE_DOC + 'def refund(order: dict) -> int:\n    """Refund an order.\n\n'
        '    Args:\n        order: the order.\n    """\n    return 1\n',
        "docstring-missing-returns",
    ),
    (
        MODULE_DOC + 'def refund(order: dict, rate: int) -> None:\n'
        '    """Refund an order.\n\n    Args:\n        order: the order.\n    """\n',
        "undocumented-param",
    ),
    (
        MODULE_DOC + 'def refund(order: dict) -> None:\n    """Refund an order.\n\n'
        '    Args:\n        order: the order.\n    """\n    raise ValueError(order)\n',
        "docstring-missing-exception",
    ),
])
def test_static_analysis_with_python_doc_comment_gap_exits_1(
    tmp_path: Path, code: str, rule: str
):
    module = tmp_path / "orders.py"
    module.write_text(code)
    result = _run(module)
    assert result.returncode == 1
    assert rule in result.stdout


@pytest.mark.parametrize("code", [
    DOCUMENTED,
    MODULE_DOC + 'def total(order: dict) -> int:\n    """Return the total."""\n'
    '    return order["total"]\n',
])
def test_static_analysis_with_python_google_style_docstring_exits_0(
    tmp_path: Path, code: str
):
    module = tmp_path / "orders.py"
    module.write_text(code)
    result = _run(module)
    assert result.returncode == 0, result.stdout + result.stderr


GO_UNDOCUMENTED = "package orders\n\nfunc Refund(total int) int {\n\treturn total\n}\n"
GO_DOCUMENTED = (
    "// Package orders refunds orders.\npackage orders\n\n"
    "// Refund returns the amount paid back for total.\n"
    "func Refund(total int) int {\n\treturn total\n}\n"
)


@pytest.mark.parametrize("code, status", [(GO_UNDOCUMENTED, 1), (GO_DOCUMENTED, 0)])
def test_static_analysis_with_go_exported_function_needs_a_doc_comment(
    tmp_path: Path, code: str, status: int
):
    source = tmp_path / "orders.go"
    source.write_text(code)
    result = _run(source)
    assert result.returncode == status, result.stdout + result.stderr
    assert ("exported function Refund should have comment" in result.stdout) == bool(status)


def test_static_analysis_with_python_test_file_skips_doc_rules(tmp_path: Path):
    test_file = tmp_path / "test_orders.py"
    test_file.write_text("def test_refund_twice_raises():\n    assert True is not False\n")
    result = _run(test_file)
    assert "undocumented-public-function" not in result.stdout
