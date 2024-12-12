"""Tests for latexify.codegen.identifier_converter."""

from __future__ import annotations

import ast

import pytest
from latexify.ast_utils import parse_expr
from latexify.codegen.identifier_converter import IdentifierConverter
from latexify.codegen.plugin_stack import Stack


@pytest.mark.parametrize(
    ("name", "use_math_symbols", "use_mathrm", "expected"),
    [
        ("a", False, True, ("a", True)),
        ("_", False, True, (r"\mathrm{\_}", False)),
        ("aa", False, True, (r"\mathrm{aa}", False)),
        ("a1", False, True, (r"\mathrm{a1}", False)),
        ("a_", False, True, (r"\mathrm{a\_}", False)),
        ("_a", False, True, (r"\mathrm{\_a}", False)),
        ("_1", False, True, (r"\mathrm{\_1}", False)),
        ("__", False, True, (r"\mathrm{\_\_}", False)),
        ("a_a", False, True, (r"\mathrm{a\_a}", False)),
        ("a__", False, True, (r"\mathrm{a\_\_}", False)),
        ("a_1", False, True, (r"\mathrm{a\_1}", False)),
        ("alpha", False, True, (r"\mathrm{alpha}", False)),
        ("alpha", True, True, (r"\alpha", True)),
        ("foo", False, True, (r"\mathrm{foo}", False)),
        ("foo", True, True, (r"\mathrm{foo}", False)),
        ("foo", True, False, (r"foo", False)),
        ("alpha_1", False, True, (r"\mathrm{alpha\_1}", False)),
    ],
)
def test_identifier_converter(name: str, use_math_symbols: bool, use_mathrm: bool, expected: tuple[str, bool]) -> None:
    assert (
        IdentifierConverter(use_math_symbols=use_math_symbols, use_mathrm=use_mathrm).convert_identifier(name)
        == expected
    )


@pytest.mark.parametrize(
    ("code", "custom", "expected"),
    [
        ("foo", {}, r"\mathrm{foo}"),
        ("foo", {"foo": r"\alpha"}, r"\alpha"),
        ("foo.bar", {}, r"\mathrm{foo}.\mathrm{bar}"),
        ("foo.bar", {"foo.bar": r"\alpha"}, r"\alpha"),
        ("alpha.beta", {}, r"\mathrm{alpha}.\mathrm{beta}"),
        ("alpha.beta", {"alpha.beta": r"\left( \overline{\beta} \right)"}, r"\left( \overline{\beta} \right)"),
    ],
)
def test_convert_identifier_custom(code: str, custom: dict[str, str], expected: str) -> None:
    expr = parse_expr(code)
    assert isinstance(expr, (ast.Name, ast.Attribute))
    visitor = Stack(IdentifierConverter(custom=custom))
    assert visitor.visit(expr) == expected
