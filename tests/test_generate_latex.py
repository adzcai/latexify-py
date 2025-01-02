"""Tests for get_latex."""

from __future__ import annotations

from latexify.generate_latex import get_latex


def test_replace_identifiers() -> None:
    def myfn(myvar):
        return 3 * myvar

    identifiers = {"myfn": "f", "myvar": "x"}

    latex_without_flag = r"\mathrm{myfn}(\mathrm{myvar}) = 3 \mathrm{myvar}"
    latex_with_flag = r"f(x) = 3 x"

    assert get_latex(myfn) == latex_without_flag
    assert get_latex(myfn, replace_identifiers=identifiers) == latex_with_flag


def test_replace_identifiers_attributes() -> None:
    def myfn(myvar):
        return 3 * np.linalg.norm(myvar)  # noqa: F821

    identifiers = {"myfn": "f", "myvar": "x", "np.linalg.norm": "foo"}

    latex_without_flag = r"\mathrm{myfn}(\mathrm{myvar}) = 3 \mathrm{np}.\mathrm{linalg}.\mathrm{norm} \mathopen{}\left( \mathrm{myvar} \mathclose{}\right)"
    latex_with_flag = r"f(x) = 3 \mathrm{foo} \mathopen{}\left( x \mathclose{}\right)"

    assert get_latex(myfn) == latex_without_flag
    assert get_latex(myfn, replace_identifiers=identifiers) == latex_with_flag


def test_prefixes() -> None:
    abc = object()

    def f(x):
        return abc.d + x.y.z.e

    latex_without_flag = r"f(x) = \mathrm{abc}.d + x.y.z.e"
    latex_with_flag1 = r"f(x) = d + x.y.z.e"
    latex_with_flag2 = r"f(x) = \mathrm{abc}.d + y.z.e"
    latex_with_flag3 = r"f(x) = \mathrm{abc}.d + z.e"
    latex_with_flag4 = r"f(x) = d + e"

    assert get_latex(f) == latex_without_flag
    assert get_latex(f, trim_prefixes=set()) == latex_without_flag
    assert get_latex(f, trim_prefixes={"abc"}) == latex_with_flag1
    assert get_latex(f, trim_prefixes={"x"}) == latex_with_flag2
    assert get_latex(f, trim_prefixes={"x.y"}) == latex_with_flag3
    assert get_latex(f, trim_prefixes={"abc", "x.y.z"}) == latex_with_flag4
    assert get_latex(f, trim_prefixes={"abc", "x", "x.y.z"}) == latex_with_flag4


def test_reduce_assignments() -> None:
    def f(x):
        y = 3 * x
        return y

    latex_without_flag = r"\begin{array}{l} y = 3 x \\ f(x) = y \end{array}"
    latex_with_flag = r"f(x) = 3 x"

    assert get_latex(f) == latex_without_flag
    assert get_latex(f, reduce_assignments=False) == latex_without_flag
    assert get_latex(f, reduce_assignments=True) == latex_with_flag


def test_reduce_assignments_with_docstring() -> None:
    def f(x):
        """DocstringRemover is required."""
        y = 3 * x
        return y

    latex_without_flag = r"\begin{array}{l} y = 3 x \\ f(x) = y \end{array}"
    latex_with_flag = r"f(x) = 3 x"

    assert get_latex(f) == latex_without_flag
    assert get_latex(f, reduce_assignments=False) == latex_without_flag
    assert get_latex(f, reduce_assignments=True) == latex_with_flag


def test_reduce_assignments_with_aug_assign() -> None:
    def f(x):
        y = 3
        y *= x
        return y

    latex_without_flag = r"\begin{array}{l} y = 3 \\ y = y x \\ f(x) = y \end{array}"
    latex_with_flag = r"f(x) = 3 x"

    assert get_latex(f) == latex_without_flag
    assert get_latex(f, reduce_assignments=False) == latex_without_flag
    assert get_latex(f, reduce_assignments=True) == latex_with_flag


def test_use_math_symbols() -> None:
    def f(alpha):
        return alpha

    latex_without_flag = r"f(\mathrm{alpha}) = \mathrm{alpha}"
    latex_with_flag = r"f(\alpha) = \alpha"

    assert get_latex(f) == latex_without_flag
    assert get_latex(f, use_math_symbols=False) == latex_without_flag
    assert get_latex(f, use_math_symbols=True) == latex_with_flag


def test_use_signature() -> None:
    def f(x):
        return x

    latex_without_flag = "x"
    latex_with_flag = r"f(x) = x"

    assert get_latex(f) == latex_with_flag
    assert get_latex(f, use_signature=False) == latex_without_flag
    assert get_latex(f, use_signature=True) == latex_with_flag


def test_use_set_symbols() -> None:
    def f(x, y):
        return x & y

    latex_without_flag = r"f(x, y) = x \mathbin{\&} y"
    latex_with_flag = r"f(x, y) = x \cap y"

    assert get_latex(f) == latex_without_flag
    assert get_latex(f, use_set_symbols=False) == latex_without_flag
    assert get_latex(f, use_set_symbols=True) == latex_with_flag
