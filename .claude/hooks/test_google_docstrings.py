"""Tests for doc_comment_guard.py: Python docstrings follow Google style 3.8.3.

A one-line docstring may leave the sections out, since Google allows that when
the name and signature say enough. A docstring of more than one line needs
Args for the parameters, Returns or Yields for a value, and Raises for each
exception the function raises itself.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from doc_comment_guard import find_violations  # noqa: E402

DETAIL = "    Orders that were already paid are skipped.\n"


def _function(signature: str, doc: str, body: str) -> str:
    return f'def {signature}:\n    """{doc}"""\n{body}\n'


ARGS = "\n    Args:\n        order: the order to cancel.\n"
RETURNS = "\n    Returns:\n        The refund.\n"
RAISES = "\n    Raises:\n        ValueError: the order is unknown.\n"

VIOLATIONS = [
    (
        _function("cancel(order)", "Cancel an order.\n\n" + DETAIL, "    pass"),
        "cancel: docstring of more than one line needs an Args: section",
    ),
    (
        _function("refund(order)", "Refund an order.\n" + ARGS, "    return order.total"),
        "refund: docstring of more than one line needs a Returns: section",
    ),
    (
        _function("lines(order)", "List the lines.\n" + ARGS, "    yield from order.lines"),
        "lines: docstring of more than one line needs a Yields: section",
    ),
    (
        _function(
            "cancel(order)", "Cancel an order.\n" + ARGS,
            "    if not order:\n        raise ValueError(order)",
        ),
        "cancel: docstring of more than one line needs a Raises: section",
    ),
    (
        _function(
            "cancel(order)", "Cancel an order.\n" + ARGS + RAISES,
            "    raise errors.PaymentError(order)",
        ),
        "cancel: Raises: section omits 'PaymentError'",
    ),
]

VALID = [
    _function("cancel(order)", "Cancel an order.", "    return order.id"),
    _function("refund(order)", "Return the refund for an order.\n" + ARGS, "    return 1"),
    _function("lines(order)", "Yields each line.\n" + ARGS, "    yield from order.lines"),
    _function("cancel(order)", "Cancel an order.\n" + ARGS, "    return None"),
    _function("refund(order)", "Refund an order.\n" + ARGS + RETURNS, "    return 1"),
    _function(
        "cancel(order)", "Cancel an order.\n" + ARGS + RAISES,
        "    raise ValueError(order)",
    ),
    _function(
        "cancel(order)", "Cancel an order.\n" + ARGS,
        "    try:\n        order.close()\n    except OSError:\n        raise",
    ),
    _function(
        "checker()", "Return a check.\n\n" + DETAIL,
        "    def check(order):\n        raise ValueError(order)\n    return check",
    ),
    'class Order:\n    """An order.\n\n    It holds lines.\n    """\n',
]


@pytest.mark.parametrize("code, expected", VIOLATIONS)
def test_find_violations_with_long_docstring_missing_a_section_reports_it(
    code: str, expected: str
):
    assert find_violations(code, "orders.py") == [expected]


@pytest.mark.parametrize("code", VALID)
def test_find_violations_with_google_style_docstring_reports_nothing(code: str):
    assert find_violations(code, "orders.py") == []


def test_find_violations_in_typescript_does_not_ask_for_google_sections():
    code = "/**\n * Cancel an order.\n *\n * Paid orders are skipped.\n */\n"
    code += "export function cancel(order: Order): number {\n  return 1;\n}\n"
    assert find_violations(code, "orders.ts") == []
