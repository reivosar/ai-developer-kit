#!/usr/bin/env python3
"""Find the public Python definitions, their docstring, and their parameters."""
import ast
import os
import sys
from typing import Iterator, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from doc_comment_shapes import Definition  # noqa: E402

_PYTHON_DEFINITIONS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
# A setter or an overload is documented on the definition it belongs to.
_DOCUMENTED_ELSEWHERE = {"setter", "deleter", "overload", "override"}


def _decorator_name(decorator: ast.expr) -> str:
    target = decorator.func if isinstance(decorator, ast.Call) else decorator
    if isinstance(target, ast.Attribute):
        return target.attr
    return target.id if isinstance(target, ast.Name) else ""


def _is_documented_elsewhere(node: ast.AST) -> bool:
    names = {_decorator_name(decorator) for decorator in node.decorator_list}
    return bool(names & _DOCUMENTED_ELSEWHERE)


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
        yield Definition(name, ast.get_docstring(node), _python_parameters(node))
        if isinstance(node, ast.ClassDef):
            yield from _public_python_nodes(node.body, name + ".")


def python_definitions(code: str) -> list[Definition]:
    """Return the public functions, methods, and classes in Python code.

    A name with a leading underscore is private. Code that does not parse
    gives an empty list.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    return list(_public_python_nodes(tree.body, ""))
