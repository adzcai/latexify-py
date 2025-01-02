"""Analyzer functions for specific subtrees."""

from __future__ import annotations

import ast
import dataclasses
import sys

from latexify.ast_utils import make_constant
from latexify.exceptions import LatexifySyntaxError


@dataclasses.dataclass(frozen=True, eq=False)
class RangeInfo:
    """Information of the range function."""

    # Argument subtrees. These arguments could be shallow copies of the original
    # subtree.
    start: ast.expr
    stop: ast.expr
    step: ast.expr

    # Integer representation of each argument, when it is possible.
    start_int: int | None
    stop_int: int | None
    step_int: int | None


def extract_int_or_none(node: ast.expr) -> int | None:
    """Extracts int constant from the given Constant node.

    Args:
        node: ast.Constant or its equivalent representing an int value.

    Returns:
        Extracted int value, or None if extraction failed.
    """
    if sys.version_info < (3, 8):
        if isinstance(node, ast.Num) and isinstance(node.n, int) and not isinstance(node.n, bool):
            return node.n
    elif isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.n, bool):
        return node.value

    return None


def analyze_range(node: ast.Call) -> RangeInfo:
    """Obtains RangeInfo from a Call subtree.

    Args:
        node: Subtree to be analyzed.

    Returns:
        RangeInfo extracted from `node`.

    Raises:
        LatexifySyntaxError: Analysis failed.
    """
    if not (isinstance(node.func, ast.Name) and node.func.id == "range" and 1 <= len(node.args) <= 3):
        raise LatexifySyntaxError("Unsupported AST for analyze_range.")

    num_args = len(node.args)

    if num_args == 1:
        start = make_constant(0)
        stop = node.args[0]
        step = make_constant(1)
    else:
        start = node.args[0]
        stop = node.args[1]
        step = node.args[2] if num_args == 3 else make_constant(1)

    return RangeInfo(
        start=start,
        stop=stop,
        step=step,
        start_int=extract_int_or_none(start),
        stop_int=extract_int_or_none(stop),
        step_int=extract_int_or_none(step),
    )


def reduce_stop_parameter(node: ast.expr) -> ast.expr:
    """Adjusts the stop expression of the range.

    This function tries to convert the syntax as follows:
        * n + 1 --> n
        * n + 2 --> n + 1
        * n - 1 --> n - 2

    Args:
        node: The target expression.

    Returns:
        Converted expression.
    """
    if not (isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub))):
        return ast.BinOp(left=node, op=ast.Sub(), right=make_constant(1))

    # Treatment for Python 3.7.
    rhs = (
        ast.Constant(value=node.right.n)
        if sys.version_info < (3, 8) and isinstance(node.right, ast.Num)
        else node.right
    )

    if not isinstance(rhs, ast.Constant):
        return ast.BinOp(left=node, op=ast.Sub(), right=make_constant(1))

    shift = 1 if isinstance(node.op, ast.Add) else -1

    return (
        node.left
        if rhs.value == shift
        else ast.BinOp(
            left=node.left,
            op=node.op,
            right=make_constant(value=rhs.value - shift),
        )
    )


def analyze_attribute(node: ast.Attribute | ast.Name) -> tuple[str, ...]:
    """Helper to obtain nested prefix.

    Args:
        node (ast.Attribute | ast.Name): Attribute or name node.

    Returns:
        The nested prefix. e.g. ("numpy", "random") for "numpy.random".
    """
    if isinstance(node, ast.Name):
        return (node.id,)

    if isinstance(node, ast.Attribute):
        return (*analyze_attribute(node.value), node.attr)

    raise LatexifySyntaxError("Unsupported AST for analyze_attribute.")


def extract_int(node: ast.expr) -> int:
    """Extracts int constant from the given Constant node.

    Args:
        node: ast.Constant or its equivalent representing an int value.

    Returns:
        Extracted int value.

    Raises:
        ValueError: Not a subtree containing an int value.
    """
    value = extract_int_or_none(node)

    if value is None:
        raise ValueError(f"Unsupported node to extract int: {type(node).__name__}")

    return value


def extract_function_name_or_none(node: ast.Call) -> str | None:
    """Extracts function name from the given Call node.

    Args:
        node (ast.Call): The function call to examine.

    Returns:
        str | None: The function name if it can be extracted, None otherwise.
    """
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None
