"""Tests for doc_comments: public definitions, their doc comment, their parameters."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from doc_comments import Definition, find_public_definitions  # noqa: E402

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
GO_ORDER = '''package orders

// Order is one customer order.
type Order struct{}

type Line struct{}

type draft struct{}

// Total returns the sum of the lines.
// It never returns a negative number.
func (o *Order) Total(rate int) int {
    return rate
}

// ApplyDiscount is separated from its function by a blank line.

func ApplyDiscount(total int) int {
    return total
}

func applyFee(total int) int {
    return total
}
'''
JAVA_ORDER = '''package shop;

/**
 * An order.
 */
public class Order {
    public static final Logger LOG = Logger.get(Order.class);

    /* Not a doc comment. */
    public Order(String id) {
    }

    /**
     * Returns the total.
     *
     * @param totals the amounts per line
     * @param rate the tax rate
     */
    @Deprecated
    @SuppressWarnings(
        "unchecked")
    public static <T> int total(Map<String, List<Integer>> totals, final int rate) {
        return rate;
    }

    public int[] sizes(String... names) {
        return null;
    }

    @Override
    public String toString() {
        return "order";
    }

    private void reset() {
    }

    void touch() {
    }
}
'''
KOTLIN_ORDER = '''package shop

/** An order. */
class Order(val id: String) {
    /**
     * Returns the total.
     * @param rate the tax rate
     */
    suspend fun total(rate: Int = 0, vararg fees: Int): Int = rate

    fun String.toOrderId(prefix: String): String = prefix + this

    override fun toString(): String = id

    private fun reset() {}

    internal fun touch() {}
}
'''
TS_ORDER = '''import { Line } from "./line";

/** Returns the discounted total. */
export function applyDiscount(total: number, rate = 0): number {
  return total - rate;
}

export const fetchOrder = async (orderId: string): Promise<Order> => {
  return load(orderId);
};

export default function first<T>(items: T[], ...rest: T[]): T {
  return items[0];
}

function parse(text: string): string {
  return text;
}

/** An order. */
@Entity()
export class Order {
  /** Returns the total. */
  public total(onDone: (result: Map<string, number>) => void, retries?: number): number {
    return 0;
  }

  public override toString(): string {
    return "order";
  }

  size(): number {
    return 0;
  }
}

export function render({ total, rate }: Props, label: string): string {
  return label;
}
'''


def _by_name(code: str, file_name: str) -> dict[str, Definition]:
    found = find_public_definitions(code, file_name)
    return {definition.name: definition for definition in found}


def test_find_public_definitions_in_python_lists_public_names_only():
    assert sorted(_by_name(PY_ORDER, "orders.py")) == [
        "Order", "Order.total", "fetch_order",
    ]


def test_find_public_definitions_in_python_reads_docstring():
    found = _by_name(PY_ORDER, "orders.py")
    assert found["Order.total"].doc == "Return the total."
    assert found["fetch_order"].doc is None


def test_find_public_definitions_in_python_reads_parameters_without_self():
    found = _by_name(PY_ORDER, "orders.py")
    assert found["Order.total"].params == (
        "rate", "rounding", "fees", "options",
    )
    assert found["Order"].params is None


def test_find_public_definitions_in_python_skips_setter_and_overload():
    found = find_public_definitions(PY_ACCESSORS, "orders.py")
    assert [definition.name for definition in found] == ["Order", "Order.total"]


def test_find_public_definitions_in_python_with_syntax_error_returns_nothing():
    assert find_public_definitions("def broken(:\n", "orders.py") == []


def test_find_public_definitions_in_go_lists_exported_names_only():
    assert sorted(_by_name(GO_ORDER, "orders.go")) == [
        "ApplyDiscount", "Line", "Order", "Total",
    ]


def test_find_public_definitions_in_go_reads_comment_lines_above():
    found = _by_name(GO_ORDER, "orders.go")
    assert found["Order"].doc == "Order is one customer order."
    assert found["Total"].doc == (
        "Total returns the sum of the lines.\n"
        "It never returns a negative number."
    )


def test_find_public_definitions_in_go_without_adjacent_comment_has_no_doc():
    found = _by_name(GO_ORDER, "orders.go")
    assert found["Line"].doc is None
    assert found["ApplyDiscount"].doc is None


def test_find_public_definitions_in_go_reads_no_parameters():
    assert _by_name(GO_ORDER, "orders.go")["Total"].params is None


def test_find_public_definitions_in_java_lists_public_names_only():
    assert sorted(_by_name(JAVA_ORDER, "Order.java")) == ["Order", "sizes", "total"]


def test_find_public_definitions_in_java_reads_javadoc_above_annotations():
    found = _by_name(JAVA_ORDER, "Order.java")
    order_class = find_public_definitions(JAVA_ORDER, "Order.java")[0]
    assert "@param rate the tax rate" in found["total"].doc
    assert (order_class.name, order_class.params) == ("Order", None)
    assert "An order." in order_class.doc


def test_find_public_definitions_in_java_ignores_plain_block_comment():
    constructors = [
        definition for definition in find_public_definitions(JAVA_ORDER, "Order.java")
        if definition.name == "Order" and definition.params is not None
    ]
    assert [constructor.doc for constructor in constructors] == [None]


def test_find_public_definitions_in_java_reads_parameter_names():
    found = _by_name(JAVA_ORDER, "Order.java")
    assert found["total"].params == ("totals", "rate")
    assert found["sizes"].params == ("names",)


def test_find_public_definitions_in_kotlin_lists_public_names_only():
    assert sorted(_by_name(KOTLIN_ORDER, "Order.kt")) == [
        "Order", "toOrderId", "total",
    ]


def test_find_public_definitions_in_kotlin_reads_kdoc_and_parameters():
    found = _by_name(KOTLIN_ORDER, "Order.kt")
    assert "@param rate the tax rate" in found["total"].doc
    assert found["total"].params == ("rate", "fees")
    assert found["toOrderId"].params == ("prefix",)
    assert found["toOrderId"].doc is None


def test_find_public_definitions_in_typescript_lists_exported_and_public_names():
    assert sorted(_by_name(TS_ORDER, "order.ts")) == [
        "Order", "applyDiscount", "fetchOrder", "first", "render", "total",
    ]


def test_find_public_definitions_in_typescript_reads_jsdoc_above_decorator():
    found = _by_name(TS_ORDER, "order.ts")
    assert found["Order"].doc == "/** An order. */"
    assert found["fetchOrder"].doc is None


def test_find_public_definitions_in_typescript_reads_parameter_names():
    found = _by_name(TS_ORDER, "order.ts")
    assert found["applyDiscount"].params == ("total", "rate")
    assert found["fetchOrder"].params == ("orderId",)
    assert found["first"].params == ("items", "rest")
    assert found["total"].params == ("onDone", "retries")


def test_find_public_definitions_in_typescript_with_destructured_parameter():
    assert _by_name(TS_ORDER, "order.ts")["render"].params is None


@pytest.mark.parametrize("file_name", ["order.rb", "order.txt", "Makefile"])
def test_find_public_definitions_in_unsupported_file_returns_nothing(file_name: str):
    assert find_public_definitions("def total\nend\n", file_name) == []
