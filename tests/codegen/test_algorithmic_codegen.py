"""Tests for latexify.codegen."""

from __future__ import annotations

import ast
import textwrap
from functools import partial

import pytest
from latexify import exceptions
from latexify.codegen.algorithmic_codegen import AlgorithmicCodegen, IPythonLatexifier
from latexify.codegen.plugin_stack import default_stack

from tests.utils import assert_latex_equal as assert_latex_equal_

visitor = default_stack(AlgorithmicCodegen())
assert_latex_equal = partial(
    assert_latex_equal_,
    visitor,
)

ipython_visitor = default_stack(IPythonLatexifier())
assert_latex_equal_ipython = partial(assert_latex_equal_, ipython_visitor)



def test_generic_visit() -> None:
    class UnknownNode(ast.AST):
        pass

    with pytest.raises(
        exceptions.LatexifyNotSupportedError,
        match=r"^Unsupported AST: UnknownNode$",
    ):
        visitor.visit(UnknownNode())


@pytest.mark.parametrize(
    ("code", "latex"),
    [
        (
            "x = 3",
            r"\State $x \gets 3$",
        ),
        (
            "a = b = 0",
            r"\State $a \gets b \gets 0$",
        ),
    ],
)
def test_visit_assign(code: str, latex: str) -> None:
    assert_latex_equal(code, ast.Assign, latex)


@pytest.mark.parametrize(
    ("code", "latex"),
    [
        (
            "for i in {1}: x = i",
            r"""
            \For{$i \in \mathopen{}\left\{ 1 \mathclose{}\right\}$}
                \State $x \gets i$
            \EndFor
            """,
        ),
    ],
)
def test_visit_for(code: str, latex: str) -> None:
    assert_latex_equal(code, ast.For, latex)


@pytest.mark.parametrize(
    ("code", "latex"),
    [
        (
            "def f(x): return x",
            r"""
            \begin{algorithmic}
                \Function{f}{$x$}
                    \State \Return $x$
                \EndFunction
            \end{algorithmic}
            """,
        ),
        (
            "def xyz(a, b, c): return 3",
            r"""
            \begin{algorithmic}
                \Function{xyz}{$a, b, c$}
                    \State \Return $3$
                \EndFunction
            \end{algorithmic}
            """,
        ),
    ],
)
def test_visit_functiondef(code: str, latex: str) -> None:
    assert_latex_equal(code, ast.FunctionDef, latex)


@pytest.mark.parametrize(
    ("code", "latex"),
    [
        (
            "if x < y: return x",
            r"""
            \If{$x < y$}
                \State \Return $x$
            \EndIf
            """,
        ),
        (
            "if True: x\nelse: y",
            r"""
            \If{$\mathrm{True}$}
                \State $x$
            \Else
                \State $y$
            \EndIf
            """,
        ),
    ],
)
def test_visit_if(code: str, latex: str) -> None:
    assert_latex_equal(code, ast.If, latex)


@pytest.mark.parametrize(
    ("code", "latex"),
    [
        # basic test
        (
            """
            if x < y:
                return x
            elif x > y:
                return y
            """,
            r"""
            \If{$x < y$}
                \State \Return $x$
            \ElsIf{$x > y$}
                \State \Return $y$
            \EndIf
            """,
        ),
        # multiple elifs
        (
            """
            if x < 5:
                return x
            elif x < 10:
                y = 0
                return y
            else:
                z = 0
                return z
            """,
            r"""
            \If{$x < 5$}
                \State \Return $x$
            \ElsIf{$x < 10$}
                \State $y \gets 0$
                \State \Return $y$
            \Else
                \State $z \gets 0$
                \State \Return $z$
            \EndIf
            """,
        ),
        # nested ifs should be detected as elifs
        (
            """
            if x < 5:
                return x
            else:
                if x < 10:
                    return y
                else:
                    return z
            """,
            r"""
            \If{$x < 5$}
                \State \Return $x$
            \ElsIf{$x < 10$}
                \State \Return $y$
            \Else
                \State \Return $z$
            \EndIf
            """,
        ),
        # else with statements should not be collapsed
        (
            """
            if x < 5:
                return x
            else:
                y = 0
                if x < 10:
                    return y
                else:
                    return z
            """,
            r"""
            \If{$x < 5$}
                \State \Return $x$
            \Else
                \State $y \gets 0$
                \If{$x < 10$}
                    \State \Return $y$
                \Else
                    \State \Return $z$
                \EndIf
            \EndIf
            """,
        ),
    ],
)
def test_visit_elif(code: str, latex: str) -> None:
    assert_latex_equal(code, ast.If, latex)


@pytest.mark.parametrize(
    ("code", "latex"),
    [
        (
            "return x + y",
            r"\State \Return $x + y$",
        ),
        (
            "return",
            r"\State \Return",
        ),
    ],
)
def test_visit_return(code: str, latex: str) -> None:
    assert_latex_equal(code, ast.Return, latex)


@pytest.mark.parametrize(
    ("code", "latex"),
    [
        (
            "while x < y: x = x + 1",
            r"""
            \While{$x < y$}
                \State $x \gets x + 1$
            \EndWhile
            """,
        )
    ],
)
def test_visit_while(code: str, latex: str) -> None:
    assert_latex_equal(code, ast.While, latex)


def test_visit_while_with_else() -> None:
    node = ast.parse(
        textwrap.dedent(
            """
            while True:
                x = x
            else:
                x = y
            """
        )
    ).body[0]
    assert isinstance(node, ast.While)
    with pytest.raises(
        exceptions.LatexifyNotSupportedError,
        match="^While statement with the else clause is not supported$",
    ):
        visitor.visit(node)


def test_visit_pass() -> None:
    assert_latex_equal("pass", ast.Pass, r"\State $\mathbf{pass}$")


def test_visit_break() -> None:
    assert_latex_equal("break", ast.Break, r"\State $\mathbf{break}$")


def test_visit_continue() -> None:
    assert_latex_equal("continue", ast.Continue, r"\State $\mathbf{continue}$")


@pytest.mark.parametrize(
    ("code", "latex"),
    [
        ("x = 3", r"x \gets 3"),
        ("a = b = 0", r"a \gets b \gets 0"),
    ],
)
def test_visit_assign_ipython(code: str, latex: str) -> None:
    assert_latex_equal_ipython(code, ast.Assign, latex)


@pytest.mark.parametrize(
    ("code", "latex"),
    [
        (
            "for i in {1}: x = i",
            (
                r"\mathbf{for} \ i \in \mathopen{}\left\{ 1 \mathclose{}\right\}"
                r" \ \mathbf{do} \\"
                r" \hspace{1em} x \gets i \\"
                r" \mathbf{end \ for}"
            ),
        ),
    ],
)
def test_visit_for_ipython(code: str, latex: str) -> None:
    assert_latex_equal_ipython(code, ast.For, latex)


@pytest.mark.parametrize(
    ("code", "latex"),
    [
        (
            "def f(x): return x",
            (
                r"\begin{array}{l}"
                r" \mathbf{function}"
                r" \ f(x) \\"
                r" \hspace{1em} \mathbf{return} \ x \\"
                r" \mathbf{end \ function}"
                r" \end{array}"
            ),
        ),
        (
            "def f(a, b, c): return 3",
            (
                r"\begin{array}{l}"
                r" \mathbf{function}"
                r" \ f(a, b, c) \\"
                r" \hspace{1em} \mathbf{return} \ 3 \\"
                r" \mathbf{end \ function}"
                r" \end{array}"
            ),
        ),
    ],
)
def test_visit_functiondef_ipython(code: str, latex: str) -> None:
    assert_latex_equal_ipython(code, ast.FunctionDef, latex)


@pytest.mark.parametrize(
    ("code", "latex"),
    [
        (
            "if x < y: return x",
            (r"\mathbf{if} \ x < y \\" r" \hspace{1em} \mathbf{return} \ x \\" r" \mathbf{end \ if}"),
        ),
        (
            "if True: x\nelse: y",
            (
                r"\mathbf{if} \ \mathrm{True} \\"
                r" \hspace{1em} x \\"
                r" \mathbf{else} \\"
                r" \hspace{1em} y \\"
                r" \mathbf{end \ if}"
            ),
        ),
    ],
)
def test_visit_if_ipython(code: str, latex: str) -> None:
    assert_latex_equal_ipython(code, ast.If, latex)


@pytest.mark.parametrize(
    ("code", "latex"),
    [
        (
            "return x + y",
            r"\mathbf{return} \ x + y",
        ),
        (
            "return",
            r"\mathbf{return}",
        ),
    ],
)
def test_visit_return_ipython(code: str, latex: str) -> None:
    assert_latex_equal_ipython(code, ast.Return, latex)


@pytest.mark.parametrize(
    ("code", "latex"),
    [
        (
            "while x < y: x = x + 1",
            (r"\mathbf{while} \ x < y \\" r" \hspace{1em} x \gets x + 1 \\" r" \mathbf{end \ while}"),
        )
    ],
)
def test_visit_while_ipython(code: str, latex: str) -> None:
    assert_latex_equal_ipython(code, ast.While, latex)


def test_visit_while_with_else_ipython() -> None:
    node = ast.parse(
        textwrap.dedent(
            """
            while True:
                x = x
            else:
                x = y
            """
        )
    ).body[0]
    assert isinstance(node, ast.While)
    with pytest.raises(
        exceptions.LatexifyNotSupportedError,
        match="^While statement with the else clause is not supported$",
    ):
        ipython_visitor.visit(node)


def test_visit_pass_ipython() -> None:
    assert_latex_equal_ipython("pass", ast.Pass, r"\mathbf{pass}")


def test_visit_break_ipython() -> None:
    assert_latex_equal_ipython("break", ast.Break, r"\mathbf{break}")


def test_visit_continue_ipython() -> None:
    assert_latex_equal_ipython("continue", ast.Continue, r"\mathbf{continue}")

