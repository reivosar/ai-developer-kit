"""Tests for doc_comments: Java, Kotlin, and TypeScript definitions and their doc comments."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from doc_comments import Definition, find_public_definitions  # noqa: E402

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
