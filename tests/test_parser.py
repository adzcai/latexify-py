"""Tests for latexify.parser."""

from __future__ import annotations

import ast

import pytest
from latexify.ast_utils import parse_function
from latexify.exceptions import LatexifySyntaxError

from tests.utils import assert_ast_equal


def test_parse_function_with_posonlyargs() -> None:
    def f(x):
        return x

    expected = ast.Module(
        body=[
            ast.FunctionDef(
                name="f",
                args=ast.arguments(
                    args=[ast.arg(arg="x")],
                ),
                body=[ast.Return(value=ast.Name(id="x", ctx=ast.Load()))],
            )
        ],
    )

    obtained = parse_function(f)
    assert_ast_equal(obtained, expected)


def test_parse_function_with_lambda() -> None:
    with pytest.raises(LatexifySyntaxError, match=r"^Not a function\.$"):
        parse_function(lambda: ())
    x = lambda: ()  # noqa: E731
    with pytest.raises(LatexifySyntaxError, match=r"^Not a function\.$"):
        parse_function(x)
