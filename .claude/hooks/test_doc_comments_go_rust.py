"""Tests for doc_comments: Go and Rust definitions and their line comments."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from doc_comments import Definition, find_public_definitions  # noqa: E402

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
RUST_ORDER = '''
/// An order and its lines.
#[derive(Debug, Clone)]
pub struct Order {
    lines: Vec<Line>,
}

pub enum Status {
    Open,
}

impl Order {
    /// Returns the total of the lines.
    /// Never negative.
    pub fn total(&self, rate: u32) -> u32 {
        rate
    }

    pub async fn fetch<T: Into<String>>(id: T) -> Order {
        todo!()
    }

    pub(crate) fn reset(&mut self) {}

    fn touch(&self) {}
}

/// A source of orders.
pub trait OrderSource {
    fn next(&mut self) -> Option<Order>;
}

// Not a doc comment.
pub const fn limit() -> u32 {
    20
}
'''


def _by_name(code: str, file_name: str) -> dict[str, Definition]:
    found = find_public_definitions(code, file_name)
    return {definition.name: definition for definition in found}


def test_find_public_definitions_in_rust_lists_pub_items_only():
    assert sorted(_by_name(RUST_ORDER, "orders.rs")) == [
        "Order", "OrderSource", "Status", "fetch", "limit", "total",
    ]


def test_find_public_definitions_in_rust_reads_doc_lines_above_attributes():
    found = _by_name(RUST_ORDER, "orders.rs")
    assert found["Order"].doc == "An order and its lines."
    assert found["total"].doc == "Returns the total of the lines.\nNever negative."


def test_find_public_definitions_in_rust_ignores_plain_comment():
    found = _by_name(RUST_ORDER, "orders.rs")
    assert found["limit"].doc is None
    assert found["Status"].doc is None
    assert found["total"].params is None


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


def test_find_public_definitions_in_python_file_reads_the_syntax_tree():
    code = 'def total(rate):\n    """Return the total."""\n    return rate\n'
    assert find_public_definitions(code, "orders.py") == [
        Definition("total", "Return the total.", ("rate",))
    ]
