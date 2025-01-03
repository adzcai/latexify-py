"""Test utilities."""

from __future__ import annotations

import ast
import functools
import sys
import textwrap
from typing import TYPE_CHECKING, cast

from latexify.ast_utils import parse_expr
from latexify.codegen.plugin_stack import _default_stack
from latexify.plugins.numpy import NumpyPlugin
from latexify.plugins.sum_prod import SumProdPlugin

if TYPE_CHECKING:
    from collections.abc import Callable

    from latexify.codegen.plugin import Plugin


visitor = _default_stack(SumProdPlugin(), NumpyPlugin())


def assert_expr_equal(src: str, tp: type[ast.AST], latex: str) -> None:
    node = parse_expr(src)
    assert isinstance(node, tp)
    assert visitor.visit(node) == latex


def assert_latex_equal(latexifier: Plugin, code: str, tp: type[ast.AST], latex: str) -> None:
    node = ast.parse(textwrap.dedent(code)).body[0]
    assert isinstance(node, tp)
    generated = latexifier.visit(node)
    assert generated == textwrap.dedent(latex).strip(), generated


def require_at_least(
    minor: int,
) -> Callable[[Callable[..., None]], Callable[..., None]]:
    """Require the minimum minor version of Python 3 to run the test.

    Args:
        minor: Minimum minor version (inclusive) that the test case supports.

    Returns:
        A decorator function to wrap the test case function.
    """

    def decorator(fn: Callable[..., None]) -> Callable[..., None]:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            if sys.version_info >= (3, minor):
                fn(*args, **kwargs)

        return wrapper

    return decorator


def require_at_most(
    minor: int,
) -> Callable[[Callable[..., None]], Callable[..., None]]:
    """Require the maximum minor version of Python 3 to run the test.

    Args:
        minor: Maximum minor version (inclusive) that the test case supports.

    Returns:
        A decorator function to wrap the test case function.
    """

    def decorator(fn: Callable[..., None]) -> Callable[..., None]:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            if sys.version_info.minor <= minor:
                fn(*args, **kwargs)

        return wrapper

    return decorator


def ast_equal(observed: ast.AST, expected: ast.AST) -> bool:
    """Checks the equality between two ASTs.

    This function checks if `observed` contains at least the same subtree with
    `expected`. If `observed` has some extra branches that `expected` does not cover,
    it is ignored.

    Args:
        observed: An AST to check.
        expected: The expected AST.

    Returns:
        True if observed and expected represent the same AST, False otherwise.
    """
    try:
        assert type(observed) is type(expected)

        for k, ve in vars(expected).items():
            if k in {"col_offset", "end_col_offset", "end_lineno", "kind", "lineno"}:
                continue

            vo = getattr(observed, k)  # May cause AttributeError.

            if isinstance(ve, ast.AST):
                assert ast_equal(cast(ast.AST, vo), ve)
            elif isinstance(ve, list):
                vo = cast(list, vo)
                assert len(vo) == len(ve)
                assert all(ast_equal(cast(ast.AST, co), cast(ast.AST, ce)) for co, ce in zip(vo, ve))
            else:
                assert type(vo) is type(ve)
                assert vo == ve

    except (AssertionError, AttributeError):
        return False

    return True


def assert_ast_equal(observed: ast.AST, expected: ast.AST) -> None:
    """Asserts the equality between two ASTs.

    Args:
        observed: An AST to compare.
        expected: Another AST.

    Raises:
        AssertionError: observed and expected represent different ASTs.
    """
    if sys.version_info >= (3, 9):
        assert ast_equal(observed, expected), f"""\
AST does not match.
observed={ast.dump(observed, indent=4)}
expected={ast.dump(expected, indent=4)}
"""
    else:
        assert ast_equal(observed, expected), f"""\
AST does not match.
observed={ast.dump(observed)}
expected={ast.dump(expected)}
"""
