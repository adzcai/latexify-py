"""Utilities to generate AST nodes."""

from __future__ import annotations

import ast
import inspect
import sys
import textwrap
from typing import TYPE_CHECKING, Any

import dill

from latexify.exceptions import LatexifySyntaxError

if TYPE_CHECKING:
    from collections.abc import Callable


def parse_expr(code: str) -> ast.expr:
    """Parses given Python expression.

    Args:
        code: Python expression to parse.

    Returns:
        ast.expr corresponding to `code`.
    """
    return ast.parse(code, mode="eval").body


def parse_function(fn: Callable[..., Any]) -> ast.Module:
    """Parses given function.

    Args:
        fn: Target function.

    Returns:
        AST tree representing `fn`.
    """
    try:
        source = inspect.getsource(fn)
    except OSError:
        # Maybe running on console.
        source = dill.source.getsource(fn)

    # Remove extra indentation so that ast.parse runs correctly.
    source = textwrap.dedent(source)
    tree = ast.parse(source)
    if not tree.body or not isinstance(tree.body[0], ast.FunctionDef):
        raise LatexifySyntaxError("Not a function.")

    return tree


def make_name(id_: str) -> ast.Name:
    """Generates a new Name node.

    Args:
        id: Name of the node.

    Returns:
        Generated ast.Name.
    """
    return ast.Name(id=id_, ctx=ast.Load())


def make_attribute(value: ast.expr, attr: str):
    """Generates a new Attribute node.

    Args:
        value: Parent value.
        attr: Attribute name.

    Returns:
        Generated ast.Attribute.
    """
    return ast.Attribute(value=value, attr=attr, ctx=ast.Load())


def make_attribute_nested(parts: tuple[str, ...]) -> ast.Attribute | ast.Name:
    """Helper to generate a new Attribute node from a nested identifier.

    Args:
        name (str): Identifier with periods (e.g. "numpy.random.randint").

    Returns:
        ast.Attribute: Generated ast.Attribute.
    """
    if len(parts) == 1:
        return make_name(parts[0])

    return make_attribute(
        make_attribute_nested(parts[:-1]),
        parts[-1],
    )


def make_constant(value: Any) -> ast.expr:
    """Generates a new Constant node.

    Args:
        value: Value of the node.

    Returns:
        Generated ast.Constant or its equivalent.

    Raises:
        ValueError: Unsupported value type.
    """
    if sys.version_info < (3, 8):
        if value is None or value is False or value is True:
            return ast.NameConstant(value=value)
        if value is ...:
            return ast.Ellipsis()
        if isinstance(value, (int, float, complex)):
            return ast.Num(n=value)
        if isinstance(value, str):
            return ast.Str(s=value)
        if isinstance(value, bytes):
            return ast.Bytes(s=value)
    elif value is None or value is ... or isinstance(value, (bool, int, float, complex, str, bytes)):
        return ast.Constant(value=value)

    raise ValueError(f"Unsupported type to generate Constant: {type(value).__name__}")


def is_constant(node: ast.AST) -> bool:
    """Checks if the node is a constant.

    Args:
        node: The node to examine.

    Returns:
        True if the node is a constant, False otherwise.
    """
    if sys.version_info < (3, 8):
        return isinstance(
            node,
            (ast.Bytes, ast.Constant, ast.Ellipsis, ast.NameConstant, ast.Num, ast.Str),
        )
    else:
        return isinstance(node, ast.Constant)


def is_str(node: ast.AST) -> bool:
    """Checks if the node is a str constant.

    Args:
        node: The node to examine.

    Returns:
        True if the node is a str constant, False otherwise.
    """
    if sys.version_info < (3, 8) and isinstance(node, ast.Str):
        return True

    return isinstance(node, ast.Constant) and isinstance(node.value, str)
