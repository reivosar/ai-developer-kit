"""Tests for function_definitions: find definitions by file extension."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from function_definitions import find_definitions  # noqa: E402


def test_find_definitions_with_python_function_returns_definition_line():
    code = "import os\n\ndef cancel_order(order_id: str) -> None:\n    pass\n"
    assert find_definitions(code, "orders.py") == {
        "cancel_order": "def cancel_order(order_id: str) -> None:"
    }


def test_find_definitions_with_indented_method_returns_stripped_line():
    code = "class Cart:\n    def add_item(self, item):\n        pass\n"
    assert find_definitions(code, "cart.py") == {
        "add_item": "def add_item(self, item):"
    }


def test_find_definitions_with_javascript_function_returns_name():
    code = "function cancelOrder(orderId) {\n  return orderId;\n}\n"
    assert set(find_definitions(code, "orders.js")) == {"cancelOrder"}


def test_find_definitions_with_go_method_returns_name():
    code = "func (c *Cart) AddItem(item Item) error {\n\treturn nil\n}\n"
    assert set(find_definitions(code, "cart.go")) == {"AddItem"}


def test_find_definitions_with_keyword_before_parenthesis_skips_keyword():
    code = "int add(int a, int b) {\n  if (a > b) {\n    return a;\n  }\n}\n"
    assert set(find_definitions(code, "sum.c")) == {"add"}


def test_find_definitions_with_one_letter_name_skips_name():
    assert find_definitions("def f():\n    pass\n", "sum.py") == {}


def test_find_definitions_with_unknown_extension_returns_empty():
    assert find_definitions("def cancel_order():\n", "notes.txt") == {}


def test_find_definitions_with_no_definition_returns_empty():
    assert find_definitions("total = price * quantity\n", "sum.py") == {}
