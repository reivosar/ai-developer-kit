"""Tests for python_doc_comments: public Python definitions read from the syntax tree."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from python_doc_comments import python_definitions  # noqa: E402

PY_ORDER = '''
class Order:
    """An order and its lines."""

    def __init__(self, lines):
        self.lines = lines

    def total(self, rate, *fees, rounding=0, **options):
        """Return the total."""
        def add(left, right):
            return left + right
        return add(rate, rounding)

    def _reset(self):
        self.lines = []


async def fetch_order(order_id):
    return order_id


def _parse(text):
    return text
'''
PY_ACCESSORS = '''
class Order:
    """An order."""

    @property
    def total(self):
        """Return the total."""
        return self._total

    @total.setter
    def total(self, value):
        self._total = value

    @typing.overload
    def find(self, key: int): ...
'''


def _by_name(code: str) -> dict:
    return {definition.name: definition for definition in python_definitions(code)}


def test_python_definitions_lists_public_names_only():
    assert sorted(_by_name(PY_ORDER)) == ["Order", "Order.total", "fetch_order"]


def test_python_definitions_reads_docstring():
    found = _by_name(PY_ORDER)
    assert found["Order.total"].doc == "Return the total."
    assert found["fetch_order"].doc is None


def test_python_definitions_reads_parameters_without_self():
    found = _by_name(PY_ORDER)
    assert found["Order.total"].params == ("rate", "rounding", "fees", "options")
    assert found["Order"].params is None


def test_python_definitions_skips_setter_and_overload():
    assert [definition.name for definition in python_definitions(PY_ACCESSORS)] == [
        "Order", "Order.total",
    ]


def test_python_definitions_with_syntax_error_returns_nothing():
    assert python_definitions("def broken(:\n") == []
