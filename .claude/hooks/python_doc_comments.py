#!/usr/bin/env python3
"""Find the public Python definitions, their docstring, and their parameters."""
import ast
import os
import sys
from typing import Iterator, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from doc_comment_shapes import Definition  # noqa: E402

_PYTHON_DEFINITIONS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
_NESTED_SCOPES = _PYTHON_DEFINITIONS + (ast.Lambda,)
# A setter or an overload is documented on the definition it belongs to.
_DOCUMENTED_ELSEWHERE = {"setter", "deleter", "overload", "override"}


def _called_name(expression: ast.expr) -> str:
    target = expression.func if isinstance(expression, ast.Call) else expression
    if isinstance(target, ast.Attribute):
        return target.attr
    return target.id if isinstance(target, ast.Name) else ""


def _is_documented_elsewhere(node: ast.AST) -> bool:
    names = {_called_name(decorator) for decorator in node.decorator_list}
    return bool(names & _DOCUMENTED_ELSEWHERE)


# A nested function's returns and raises belong to that function, not this one.
def _own_nodes(node: ast.AST) -> Iterator[ast.AST]:
    pending = list(node.body)
    while pending:
        child = pending.pop()
        yield child
        if not isinstance(child, _NESTED_SCOPES):
            pending.extend(ast.iter_child_nodes(child))


def _returns_value(node: ast.AST) -> bool:
    return any(
        isinstance(child, ast.Return) and child.value is not None
        and not (isinstance(child.value, ast.Constant) and child.value.value is None)
        for child in _own_nodes(node)
    )


def _yields(node: ast.AST) -> bool:
    return any(isinstance(child, (ast.Yield, ast.YieldFrom)) for child in _own_nodes(node))


# A bare raise passes on an exception the caller already had.
def _raised_names(node: ast.AST) -> tuple:
    names = [
        _called_name(child.exc) for child in _own_nodes(node)
        if isinstance(child, ast.Raise) and child.exc is not None
    ]
    return tuple(dict.fromkeys(name for name in names if name))


def _definition(node: ast.AST, name: str) -> Definition:
    doc = ast.get_docstring(node)
    if isinstance(node, ast.ClassDef):
        return Definition(name, doc, None)
    return Definition(
        name, doc, _python_parameters(node), _returns_value(node), _yields(node),
        _raised_names(node),
    )


def _python_parameters(node: ast.AST) -> Optional[tuple]:
    if isinstance(node, ast.ClassDef):
        return None
    arguments = node.args
    named = arguments.posonlyargs + arguments.args + arguments.kwonlyargs
    collectors = [arguments.vararg, arguments.kwarg]
    names = [argument.arg for argument in named + collectors if argument]
    return tuple(name for name in names if name not in ("self", "cls"))


def _public_python_nodes(nodes: list, prefix: str) -> Iterator[Definition]:
    for node in nodes:
        if not isinstance(node, _PYTHON_DEFINITIONS) or node.name.startswith("_"):
            continue
        if _is_documented_elsewhere(node):
            continue
        name = prefix + node.name
        yield _definition(node, name)
        if isinstance(node, ast.ClassDef):
            yield from _public_python_nodes(node.body, name + ".")


def python_definitions(code: str) -> list[Definition]:
    """Return the public functions, methods, and classes in Python code.

    A name with a leading underscore is private. Code that does not parse
    gives an empty list.

    Args:
        code: the Python source text.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    return list(_public_python_nodes(tree.body, ""))
