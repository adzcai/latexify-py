"""Tests for latexify.codegen.function_codegen."""

from __future__ import annotations

import ast
import textwrap

import pytest
from latexify import exceptions
from latexify.codegen.function_codegen import FunctionCodegen
from latexify.codegen.plugin_stack import _default_stack

visitor = _default_stack(FunctionCodegen())


def test_generic_visit() -> None:
    class UnknownNode(ast.AST):
        pass

    with pytest.raises(
        exceptions.LatexifyNotSupportedError,
        match=r"^Unsupported AST: UnknownNode$",
    ):
        visitor.visit(UnknownNode())


def test_visit_functiondef_use_signature() -> None:
    tree = ast.parse(
        textwrap.dedent(
            """
            def f(x):
                return x
            """
        )
    ).body[0]
    assert isinstance(tree, ast.FunctionDef)

    latex_without_flag = "x"
    latex_with_flag = r"f(x) = x"
    assert visitor.visit(tree) == latex_with_flag
    assert _default_stack(FunctionCodegen(use_signature=False)).visit(tree) == latex_without_flag
    assert _default_stack(FunctionCodegen(use_signature=True)).visit(tree) == latex_with_flag


def test_visit_functiondef_ignore_docstring() -> None:
    tree = ast.parse(
        textwrap.dedent(
            """
            def f(x):
                '''docstring'''
                return x
            """
        )
    ).body[0]
    assert isinstance(tree, ast.FunctionDef)

    latex = r"f(x) = x"
    assert visitor.visit(tree) == latex


def test_visit_functiondef_ignore_multiple_constants() -> None:
    tree = ast.parse(
        textwrap.dedent(
            """
            def f(x):
                '''docstring'''
                3
                True
                return x
            """
        )
    ).body[0]
    assert isinstance(tree, ast.FunctionDef)

    latex = r"f(x) = x"
    assert visitor.visit(tree) == latex
