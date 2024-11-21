"""End-to-end test cases of function."""

# ruff: noqa: B018

from __future__ import annotations

import math

from tests.integration.utils import check_function


def test_quadratic_solution() -> None:
    def solve(a, b, c):
        return (-b + math.sqrt(b**2 - 4 * a * c)) / (2 * a)

    latex = r"\mathrm{solve}(a, b, c) =" r" \frac{-b + \sqrt{ b^{2} - 4 a c }}{2 a}"
    check_function(solve, latex)


def test_sinc() -> None:
    def sinc(x):
        if x == 0:
            return 1
        else:
            return math.sin(x) / x

    latex = (
        r"\mathrm{sinc}(x) ="
        r" \left\{ \begin{array}{ll}"
        r" 1, & \mathrm{if} \ x = 0 \\"
        r" \frac{\sin x}{x}, & \mathrm{otherwise}"
        r" \end{array} \right."
    )
    check_function(sinc, latex)


def test_x_times_beta() -> None:
    def xtimesbeta(x, beta):
        return x * beta

    latex_without_symbols = r"\mathrm{xtimesbeta}(x, \mathrm{beta}) = x \cdot \mathrm{beta}"
    check_function(xtimesbeta, latex_without_symbols)
    check_function(xtimesbeta, latex_without_symbols, use_math_symbols=False)

    latex_with_symbols = r"\mathrm{xtimesbeta}(x, \beta) = x \beta"
    check_function(xtimesbeta, latex_with_symbols, use_math_symbols=True)


def test_nested_function() -> None:
    def nested(x):
        return 3 * x

    check_function(nested, r"\mathrm{nested}(x) = 3 x")


def test_double_nested_function() -> None:
    def nested(x):
        def inner(y):
            return x * y

        return inner

    check_function(nested(3), r"\mathrm{inner}(y) = x y")


def test_reduce_assignments() -> None:
    def f(x):
        a = x + x
        return 3 * a

    check_function(
        f,
        r"\begin{array}{l} a = x + x \\ f(x) = 3 a \end{array}",
    )
    check_function(
        f,
        r"f(x) = 3 \mathopen{}\left( x + x \mathclose{}\right)",
        reduce_assignments=True,
    )


def test_reduce_assignments_double() -> None:
    def f(x):
        a = x**2
        b = a + a
        return 3 * b

    latex_without_option = r"\begin{array}{l}" r" a = x^{2} \\" r" b = a + a \\" r" f(x) = 3 b" r" \end{array}"

    check_function(f, latex_without_option)
    check_function(f, latex_without_option, reduce_assignments=False)
    check_function(
        f,
        r"f(x) = 3 \mathopen{}\left( x^{2} + x^{2} \mathclose{}\right)",
        reduce_assignments=True,
    )


def test_reduce_assignments_with_if() -> None:
    def sigmoid(x):
        p = 1 / (1 + math.exp(-x))
        n = math.exp(x) / (math.exp(x) + 1)
        if x > 0:
            return p
        else:
            return n

    check_function(
        sigmoid,
        (
            r"\mathrm{sigmoid}(x) = \left\{ \begin{array}{ll}"
            r" \frac{1}{1 + \exp \mathopen{}\left( -x \mathclose{}\right)}, &"
            r" \mathrm{if} \ x > 0 \\"
            r" \frac{\exp x}{\exp x + 1}, &"
            r" \mathrm{otherwise}"
            r" \end{array} \right."
        ),
        reduce_assignments=True,
    )


def test_sub_bracket() -> None:
    def solve(a, b):
        return ((a + b) - b) / (a - b) - (a + b) - (a - b) - (a * b)

    latex = (
        r"\mathrm{solve}(a, b) ="
        r" \frac{a + b - b}{a - b} - \mathopen{}\left("
        r" a + b \mathclose{}\right) - \mathopen{}\left("
        r" a - b \mathclose{}\right) - a b"
    )
    check_function(solve, latex)


def test_docstring_allowed() -> None:
    def solve(x):
        """The identity function."""
        return x

    latex = r"\mathrm{solve}(x) = x"
    check_function(solve, latex)


def test_multiple_constants_allowed() -> None:
    def solve(x):
        """The identity function."""
        123
        True
        return x

    latex = r"\mathrm{solve}(x) = x"
    check_function(solve, latex)
