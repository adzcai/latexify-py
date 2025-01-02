"""Tests for FunctionCodegen with match statements."""

from __future__ import annotations

import ast
import textwrap

import pytest
from latexify import exceptions
from latexify.ast_utils import parse_function
from latexify.codegen.function_codegen import FunctionCodegen
from latexify.codegen.plugin_stack import _default_stack

from tests import utils

visitor = _default_stack(FunctionCodegen())


@utils.require_at_least(10)
def test_functiondef_match() -> None:
    def f(x):
        match x:
            case 0:
                return 1
            case _:
                return 3 * x

    tree = parse_function(f)
    expected = (
        r"f(x) ="
        r" \left\{ \begin{array}{ll}"
        r" 1, & \mathrm{if} \ x = 0 \\"
        r" 3 x, & \mathrm{otherwise}"
        r" \end{array} \right."
    )
    assert visitor.visit(tree) == expected


@utils.require_at_least(10)
def test_matchvalue() -> None:
    src = """
    match x:
        case 0:
            return 1
        case _:
            return 2
    """
    expected = (
        r"\left\{ \begin{array}{ll}" r" 1, & \mathrm{if} \ x = 0 \\" r" 2, & \mathrm{otherwise}" r" \end{array} \right."
    )
    utils.assert_latex_equal(visitor, src, ast.Match, expected)


@utils.require_at_least(10)
def test_multiple_matchvalue() -> None:
    src = """
    match x:
        case 0:
            return 1
        case 1:
            return 2
        case _:
            return 3
    """
    expected = (
        r"\left\{ \begin{array}{ll}"
        r" 1, & \mathrm{if} \ x = 0 \\"
        r" 2, & \mathrm{if} \ x = 1 \\"
        r" 3, & \mathrm{otherwise}"
        r" \end{array} \right."
    )
    utils.assert_latex_equal(visitor, src, ast.Match, expected)


@utils.require_at_least(10)
def test_single_matchvalue_no_wildcards() -> None:
    tree = ast.parse(
        textwrap.dedent(
            """
            match x:
                case 0:
                    return 1
            """
        )
    ).body[0]

    with pytest.raises(
        exceptions.LatexifySyntaxError,
        match=r"^Match statement must contain the wildcard\.$",
    ):
        visitor.visit(tree)


@utils.require_at_least(10)
def test_multiple_matchvalue_no_wildcards() -> None:
    tree = ast.parse(
        textwrap.dedent(
            """
            match x:
                case 0:
                    return 1
                case 1:
                    return 2
            """
        )
    ).body[0]

    with pytest.raises(
        exceptions.LatexifySyntaxError,
        match=r"^Match statement must contain the wildcard\.$",
    ):
        visitor.visit(tree)


@utils.require_at_least(10)
def test_matchas_nonempty() -> None:
    tree = ast.parse(
        textwrap.dedent(
            """
            match x:
                case [x] as y:
                    return 1
                case _:
                    return 2
            """
        )
    ).body[0]

    with pytest.raises(
        exceptions.LatexifyNotSupportedError,
        match=r"^Unsupported AST: MatchAs$",
    ):
        visitor.visit(tree)


@utils.require_at_least(10)
def test_matchvalue_no_return() -> None:
    tree = ast.parse(
        textwrap.dedent(
            """
            match x:
                case 0:
                    x = 5
                case _:
                    return 0
            """
        )
    ).body[0]

    with pytest.raises(
        exceptions.LatexifyNotSupportedError,
        match=r"^Match cases must contain exactly 1 return statement\.$",
    ):
        visitor.visit(tree)


@utils.require_at_least(10)
def test_matchvalue_mutliple_statements() -> None:
    tree = ast.parse(
        textwrap.dedent(
            """
            match x:
                case 0:
                    x = 5
                    return 1
                case _:
                    return 0
            """
        )
    ).body[0]

    with pytest.raises(
        exceptions.LatexifyNotSupportedError,
        match=r"^Match cases must contain exactly 1 return statement\.$",
    ):
        visitor.visit(tree)
