import ast
import math
from functools import partial

import pytest
from latexify.plugins.sum_prod import SumProdPlugin

from tests.integration.utils import check_function
from tests.utils import assert_expr_equal

check_function_sum_prod = partial(check_function, plugins=[SumProdPlugin()])


@pytest.mark.parametrize(
    ("src_suffix", "dest_suffix"),
    [
        # No arguments
        ("()", r" \mathopen{}\left( \mathclose{}\right)"),
        # No comprehension
        ("(x)", r" x"),
        (
            "([1, 2])",
            r" \mathopen{}\left[ 1, 2 \mathclose{}\right]",
        ),
        (
            "({1, 2})",
            r" \mathopen{}\left\{ 1, 2 \mathclose{}\right\}",
        ),
        ("(f(x))", r" f \mathopen{}\left( x \mathclose{}\right)"),
        # Single comprehension
        ("(i for i in x)", r"_{i \in x}^{} \mathopen{}\left({i}\mathclose{}\right)"),
        (
            "(i for i in [1, 2])",
            r"_{i \in \mathopen{}\left[ 1, 2 \mathclose{}\right]}^{} " r"\mathopen{}\left({i}\mathclose{}\right)",
        ),
        (
            "(i for i in {1, 2})",
            r"_{i \in \mathopen{}\left\{ 1, 2 \mathclose{}\right\}}^{}" r" \mathopen{}\left({i}\mathclose{}\right)",
        ),
        (
            "(i for i in f(x))",
            r"_{i \in f \mathopen{}\left( x \mathclose{}\right)}^{}" r" \mathopen{}\left({i}\mathclose{}\right)",
        ),
    ],
)
def test_iterables(src_suffix: str, dest_suffix: str) -> None:
    for src_fn, dest_fn in [("fsum", r"\sum"), ("sum", r"\sum"), ("prod", r"\prod")]:
        assert_expr_equal(src_fn + src_suffix, ast.Call, dest_fn + dest_suffix)


@pytest.mark.parametrize(
    ("src_suffix", "dest_suffix"),
    [
        (
            "(i for i in range(n))",
            r"_{i = 0}^{n - 1} \mathopen{}\left({i}\mathclose{}\right)",
        ),
        (
            "(i for i in range(n + 1))",
            r"_{i = 0}^{n} \mathopen{}\left({i}\mathclose{}\right)",
        ),
        (
            "(i for i in range(n + 2))",
            r"_{i = 0}^{n + 1} \mathopen{}\left({i}\mathclose{}\right)",
        ),
        (
            # ast.parse() does not recognize negative integers.
            "(i for i in range(n - -1))",
            r"_{i = 0}^{n - -1 - 1} \mathopen{}\left({i}\mathclose{}\right)",
        ),
        (
            "(i for i in range(n - 1))",
            r"_{i = 0}^{n - 2} \mathopen{}\left({i}\mathclose{}\right)",
        ),
        (
            "(i for i in range(n + m))",
            r"_{i = 0}^{n + m - 1} \mathopen{}\left({i}\mathclose{}\right)",
        ),
        (
            "(i for i in range(n - m))",
            r"_{i = 0}^{n - m - 1} \mathopen{}\left({i}\mathclose{}\right)",
        ),
        (
            "(i for i in range(3))",
            r"_{i = 0}^{2} \mathopen{}\left({i}\mathclose{}\right)",
        ),
        (
            "(i for i in range(3 + 1))",
            r"_{i = 0}^{3} \mathopen{}\left({i}\mathclose{}\right)",
        ),
        (
            "(i for i in range(3 + 2))",
            r"_{i = 0}^{3 + 1} \mathopen{}\left({i}\mathclose{}\right)",
        ),
        (
            "(i for i in range(3 - 1))",
            r"_{i = 0}^{3 - 2} \mathopen{}\left({i}\mathclose{}\right)",
        ),
        (
            # ast.parse() does not recognize negative integers.
            "(i for i in range(3 - -1))",
            r"_{i = 0}^{3 - -1 - 1} \mathopen{}\left({i}\mathclose{}\right)",
        ),
        (
            "(i for i in range(3 + m))",
            r"_{i = 0}^{3 + m - 1} \mathopen{}\left({i}\mathclose{}\right)",
        ),
        (
            "(i for i in range(3 - m))",
            r"_{i = 0}^{3 - m - 1} \mathopen{}\left({i}\mathclose{}\right)",
        ),
        (
            "(i for i in range(n, m))",
            r"_{i = n}^{m - 1} \mathopen{}\left({i}\mathclose{}\right)",
        ),
        (
            "(i for i in range(1, m))",
            r"_{i = 1}^{m - 1} \mathopen{}\left({i}\mathclose{}\right)",
        ),
        (
            "(i for i in range(n, 3))",
            r"_{i = n}^{2} \mathopen{}\left({i}\mathclose{}\right)",
        ),
        (
            "(i for i in range(n, m, k))",
            r"_{i \in \mathrm{range} \mathopen{}\left( n, m, k \mathclose{}\right)}^{}"
            r" \mathopen{}\left({i}\mathclose{}\right)",
        ),
    ],
)
def test_ranges(src_suffix: str, dest_suffix: str) -> None:
    for src_fn, dest_fn in [("fsum", r"\sum"), ("sum", r"\sum"), ("prod", r"\prod")]:
        assert_expr_equal(src_fn + src_suffix, ast.Call, dest_fn + dest_suffix)


@pytest.mark.parametrize(
    ("code", "latex"),
    [
        # 2 clauses
        (
            "sum(i for y in x for i in y)",
            r"\sum_{y \in x}^{} \sum_{i \in y}^{} " r"\mathopen{}\left({i}\mathclose{}\right)",
        ),
        (
            "sum(i for y in x for z in y for i in z)",
            r"\sum_{y \in x}^{} \sum_{z \in y}^{} \sum_{i \in z}^{} " r"\mathopen{}\left({i}\mathclose{}\right)",
        ),
        # 3 clauses
        (
            "prod(i for y in x for i in y)",
            r"\prod_{y \in x}^{} \prod_{i \in y}^{} " r"\mathopen{}\left({i}\mathclose{}\right)",
        ),
        (
            "prod(i for y in x for z in y for i in z)",
            r"\prod_{y \in x}^{} \prod_{z \in y}^{} \prod_{i \in z}^{} " r"\mathopen{}\left({i}\mathclose{}\right)",
        ),
        # reduce stop parameter
        (
            "sum(i for i in range(n+1))",
            r"\sum_{i = 0}^{n} \mathopen{}\left({i}\mathclose{}\right)",
        ),
        (
            "prod(i for i in range(n-1))",
            r"\prod_{i = 0}^{n - 2} \mathopen{}\left({i}\mathclose{}\right)",
        ),
    ],
)
def test_visit_call_sum_prod_multiple_comprehension(code: str, latex: str) -> None:
    assert_expr_equal(code, ast.Call, latex)


@pytest.mark.parametrize(
    ("src_suffix", "dest_suffix"),
    [
        (
            "(i for i in x if i < y)",
            r"_{\mathopen{}\left( i \in x \mathclose{}\right) "
            r"\land \mathopen{}\left( i < y \mathclose{}\right)}^{} "
            r"\mathopen{}\left({i}\mathclose{}\right)",
        ),
        (
            "(i for i in x if i < y if f(i))",
            r"_{\mathopen{}\left( i \in x \mathclose{}\right)"
            r" \land \mathopen{}\left( i < y \mathclose{}\right)"
            r" \land \mathopen{}\left( f \mathopen{}\left("
            r" i \mathclose{}\right) \mathclose{}\right)}^{}"
            r" \mathopen{}\left({i}\mathclose{}\right)",
        ),
    ],
)
def test_visit_call_sum_prod_with_if(src_suffix: str, dest_suffix: str) -> None:
    for src_fn, dest_fn in [("sum", r"\sum"), ("prod", r"\prod")]:
        assert_expr_equal(src_fn + src_suffix, ast.Call, dest_fn + dest_suffix)


def test_sum_with_limit_1arg() -> None:
    def sum_with_limit(n):
        return sum(i**2 for i in range(n))

    latex = r"\mathrm{sum\_with\_limit}(n) = \sum_{i = 0}^{n - 1}" r" \mathopen{}\left({i^{2}}\mathclose{}\right)"
    check_function_sum_prod(sum_with_limit, latex)


def test_sum_with_limit_2args() -> None:
    def sum_with_limit(a, n):
        return sum(i**2 for i in range(a, n))

    latex = r"\mathrm{sum\_with\_limit}(a, n) = \sum_{i = a}^{n - 1}" r" \mathopen{}\left({i^{2}}\mathclose{}\right)"
    check_function_sum_prod(sum_with_limit, latex)


def test_sum_with_reducible_limit() -> None:
    def sum_with_limit(n):
        return sum(i for i in range(n + 1))

    latex = r"\mathrm{sum\_with\_limit}(n) = \sum_{i = 0}^{n}" r" \mathopen{}\left({i}\mathclose{}\right)"
    check_function_sum_prod(sum_with_limit, latex)


def test_sum_with_irreducible_limit() -> None:
    def sum_with_limit(n):
        return sum(i for i in range(n * 3))

    latex = r"\mathrm{sum\_with\_limit}(n) = \sum_{i = 0}^{n \cdot 3 - 1}" r" \mathopen{}\left({i}\mathclose{}\right)"
    check_function_sum_prod(sum_with_limit, latex)


def test_prod_with_limit_1arg() -> None:
    def prod_with_limit(n):
        return math.prod(i**2 for i in range(n))

    latex = r"\mathrm{prod\_with\_limit}(n) =" r" \prod_{i = 0}^{n - 1} \mathopen{}\left({i^{2}}\mathclose{}\right)"
    check_function_sum_prod(prod_with_limit, latex)


def test_prod_with_limit_2args() -> None:
    def prod_with_limit(a, n):
        return math.prod(i**2 for i in range(a, n))

    latex = r"\mathrm{prod\_with\_limit}(a, n) =" r" \prod_{i = a}^{n - 1} \mathopen{}\left({i^{2}}\mathclose{}\right)"
    check_function_sum_prod(prod_with_limit, latex)


def test_prod_with_reducible_limits() -> None:
    def prod_with_limit(n):
        return math.prod(i for i in range(n - 1))

    latex = r"\mathrm{prod\_with\_limit}(n) =" r" \prod_{i = 0}^{n - 2} \mathopen{}\left({i}\mathclose{}\right)"
    check_function_sum_prod(prod_with_limit, latex)


def test_prod_with_irreducible_limit() -> None:
    def prod_with_limit(n):
        return math.prod(i for i in range(n * 3))

    latex = r"\mathrm{prod\_with\_limit}(n) = " r"\prod_{i = 0}^{n \cdot 3 - 1} \mathopen{}\left({i}\mathclose{}\right)"
    check_function_sum_prod(prod_with_limit, latex)
