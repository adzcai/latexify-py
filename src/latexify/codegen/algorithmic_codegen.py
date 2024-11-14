"""Codegen for single algorithms."""

from __future__ import annotations

import ast
import contextlib
from typing import TYPE_CHECKING

from latexify import exceptions
from latexify.codegen.expression_codegen import ExpressionCodegen
from latexify.codegen.identifier_converter import IdentifierConverter

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable


class AlgorithmicCodegen(ast.NodeVisitor):
    """Codegen for single algorithms.

    This subclasses the ast.NodeVisitor
    to take in an AST rooted at a single FunctionDef node
    and generate LaTeX `algpseudocode` code for the algorithm.

    If `ipython` is enabled,
    doesn't use the `algorithmic` environment.

    This codegen works for Module with single FunctionDef node to generate a single
    LaTeX expression of the given algorithm.
    """

    _identifier_converter: IdentifierConverter
    _indent_level: int
    SPACES_PER_INDENT = 4
    EM_PER_INDENT = 1

    def __init__(
        self,
        *,
        use_math_symbols: bool = False,
        use_set_symbols: bool = False,
        ipython: bool = False,
    ) -> None:
        """Initializer.

        Args:
            use_math_symbols: Whether to convert identifiers with a math symbol surface
                (e.g., "alpha") to the LaTeX symbol (e.g., "\\alpha").
            use_set_symbols: Whether to use set symbols or not.
        """
        self._expression_codegen = ExpressionCodegen(use_math_symbols=use_math_symbols, use_set_symbols=use_set_symbols)
        self._identifier_converter = IdentifierConverter(use_math_symbols=use_math_symbols, use_mathrm=ipython)
        self._indent_level = 0
        self.LINE_BREAK = r" \\ " if ipython else "\n"
        self._ipython = ipython

    def generic_visit(self, node: ast.AST) -> str:
        raise exceptions.LatexifyNotSupportedError(f"Unsupported AST: {type(node).__name__}")

    def _state(self, line: str) -> str:
        if self._ipython:
            return self.add_indent(line)
        else:
            return self.add_indent(rf"\State ${line}$")

    def _expr(self, node: ast.AST) -> str:
        return self._expression_codegen.visit(node)

    def visit_Assign(self, node: ast.Assign) -> str:
        """Visit an Assign node."""
        return self._state(r" \gets ".join(map(self._expr, (*node.targets, node.value))))

    def visit_Expr(self, node: ast.Expr) -> str:
        """Visit an Expr node."""
        return self._state(self._expr(node.value))

    def visit_For(self, node: ast.For) -> str:
        """Visit a For node."""
        if len(node.orelse) != 0:
            raise exceptions.LatexifyNotSupportedError("For statement with the else clause is not supported")

        target_latex, iter_latex = self._expr(node.target), self._expr(node.iter)
        block = IndentedBlock(self)
        block.add(
            rf"\mathbf{{for}} \ {target_latex} \in {iter_latex} \ \mathbf{{do}}"
            if self._ipython
            else f"\\For{{${target_latex} \\in {iter_latex}$}}"
        )
        with self._increment_level():
            block.extend(node.body)

        block.add(r"\mathbf{end \ for}" if self._ipython else r"\EndFor")
        return str(block)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> str:
        """Visit a FunctionDef node."""
        name_latex = self._identifier_converter.convert(node.name)[0]

        # Arguments
        arg_latex = [self._identifier_converter.convert(arg.arg)[0] for arg in node.args.args]

        top = self._indent_level == 0

        if self._ipython:
            block = IndentedBlock(self)
            block.add(
                (r"\begin{array}{l} " if top else "") + rf"\mathbf{{function}} \ {name_latex}({', '.join(arg_latex)})"
            )
            with self._increment_level():
                block.extend(node.body)
            block.add(r"\mathbf{end \ function}" + (r" \end{array}" if top else ""))

        else:
            block = IndentedBlock(self)
            if top:
                block.add(r"\begin{algorithmic}")
            with self._increment_level():
                block.add(f"\\Function{{{name_latex}}}{{${', '.join(arg_latex)}$}}")
                with self._increment_level():
                    block.extend(node.body)
                block.add(r"\EndFunction")
            if top:
                block.add(r"\end{algorithmic}")

        return str(block)

    def visit_If(self, node: ast.If) -> str:
        """Visit an If node."""

        branches = [node]
        while len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
            branches.append(node := node.orelse[0])

        block = IndentedBlock(self)
        # if and elif statements
        for i, branch in enumerate(branches):
            # test
            cond_latex = self._expr(branch.test)
            command = (
                (r"\If" if i == 0 else r"\ElsIf")
                if not self._ipython
                else (r"\mathbf{if}" if i == 0 else r"\mathbf{else if}")
            )
            block.add(f"{command}{{${cond_latex}$}}" if not self._ipython else rf"{command} \ {cond_latex}")

            # body
            with self._increment_level():
                block.extend(branch.body)

        # else
        if node.orelse:
            block.add(r"\Else" if not self._ipython else r"\mathbf{else}")
            with self._increment_level():
                block.extend(node.orelse)

        block.add(r"\EndIf" if not self._ipython else r"\mathbf{end \ if}")
        return str(block)

    def visit_Module(self, node: ast.Module) -> str:
        """Visit a Module node."""
        return self.visit(node.body[0])

    def visit_Return(self, node: ast.Return) -> str:
        """Visit a Return node."""
        return self.add_indent(
            (
                rf"\State \Return ${self._expr(node.value)}$"
                if not self._ipython
                else r"\mathbf{return} \ " + self._expr(node.value)
            )
            if node.value is not None
            else (r"\State \Return" if not self._ipython else r"\mathbf{return}")
        )

    def visit_While(self, node: ast.While) -> str:
        """Visit a While node."""
        if node.orelse:
            raise exceptions.LatexifyNotSupportedError("While statement with the else clause is not supported")
        block = IndentedBlock(self)
        block.add(
            f"\\While{{${self._expr(node.test)}$}}"
            if not self._ipython
            else r"\mathbf{while} \ " + self._expr(node.test)
        )
        with self._increment_level():
            block.extend(node.body)
        block.add(r"\EndWhile" if not self._ipython else r"\mathbf{end \ while}")
        return str(block)

    def visit_Pass(self, _node: ast.Pass) -> str:
        """Visit a Pass node."""
        return self._state(r"\mathbf{pass}")

    def visit_Break(self, _node: ast.Break) -> str:
        """Visit a Break node."""
        return self._state(r"\mathbf{break}")

    def visit_Continue(self, _node: ast.Continue) -> str:
        """Visit a Continue node."""
        return self._state(r"\mathbf{continue}")

    @contextlib.contextmanager
    def _increment_level(self) -> Generator[None, None, None]:
        """Context manager controlling indent level."""
        self._indent_level += 1
        yield
        self._indent_level -= 1

    def add_indent(self, line: str) -> str:
        """Adds an indent before the line.

        Args:
            line: The line to add an indent to.
        """
        if self._ipython:
            return rf"\hspace{{{self._indent_level * self.EM_PER_INDENT}em}} {line}" if self._indent_level > 0 else line
        else:
            return self._indent_level * self.SPACES_PER_INDENT * " " + line


class IndentedBlock:
    _items: list[str]
    _visitor: AlgorithmicCodegen

    def __init__(self, visitor) -> None:
        self._items = []
        self._visitor = visitor

    def add(self, item: str | ast.AST) -> None:
        self._items.append(self._fmt(item))

    def extend(self, items: Iterable[str | ast.AST]) -> None:
        self._items.extend(map(self._fmt, items))

    def _fmt(self, item: str | ast.AST) -> str:
        return self._visitor.add_indent(item) if isinstance(item, str) else self._visitor.visit(item)

    def __str__(self) -> str:
        return self._visitor.LINE_BREAK.join(self._items)
