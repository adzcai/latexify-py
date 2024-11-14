"""Codegen for single algorithms."""

from __future__ import annotations

import ast
import contextlib
from typing import TYPE_CHECKING

from latexify import exceptions
from latexify.codegen.expression_codegen import ExpressionCodegen
from latexify.codegen.identifier_converter import IdentifierConverter

if TYPE_CHECKING:
    from collections.abc import Generator


class AlgorithmicCodegen(ast.NodeVisitor):
    """Codegen for single algorithms.

    This subclasses the ast.NodeVisitor
    to take in an AST rooted at a single FunctionDef node
    and generate LaTeX `algpseudocode` code for the algorithm.
    """

    SPACES_PER_INDENT = 4

    _identifier_converter: IdentifierConverter
    _indent_level: int

    def __init__(self, *, use_math_symbols: bool = False, use_set_symbols: bool = False) -> None:
        """Initializer.

        Args:
            use_math_symbols: Whether to convert identifiers with a math symbol surface
                (e.g., "alpha") to the LaTeX symbol (e.g., "\\alpha").
            use_set_symbols: Whether to use set symbols or not.
        """
        self._expression_codegen = ExpressionCodegen(use_math_symbols=use_math_symbols, use_set_symbols=use_set_symbols)
        self._identifier_converter = IdentifierConverter(
            use_math_symbols=use_math_symbols,
            use_mathrm=False,
        )
        self._indent_level = 0

    def generic_visit(self, node: ast.AST) -> str:
        raise exceptions.LatexifyNotSupportedError(f"Unsupported AST: {type(node).__name__}")

    def visit_Assign(self, node: ast.Assign) -> str:
        """Visit an Assign node."""
        operands: list[str] = [self._expression_codegen.visit(target) for target in node.targets]
        operands.append(self._expression_codegen.visit(node.value))
        operands_latex = r" \gets ".join(operands)
        return self._add_indent(rf"\State ${operands_latex}$")

    def visit_Expr(self, node: ast.Expr) -> str:
        """Visit an Expr node."""
        return self._add_indent(rf"\State ${self._expression_codegen.visit(node.value)}$")

    def visit_For(self, node: ast.For) -> str:
        """Visit a For node."""
        if len(node.orelse) != 0:
            raise exceptions.LatexifyNotSupportedError("For statement with the else clause is not supported")

        target_latex = self._expression_codegen.visit(node.target)
        iter_latex = self._expression_codegen.visit(node.iter)
        with self._increment_level():
            body_latex = "\n".join(self.visit(stmt) for stmt in node.body)

        return (
            self._add_indent(f"\\For{{${target_latex} \\in {iter_latex}$}}\n")
            + f"{body_latex}\n"
            + self._add_indent("\\EndFor")
        )

    # TODO(ZibingZhang): support nested functions
    def visit_FunctionDef(self, node: ast.FunctionDef) -> str:
        """Visit a FunctionDef node."""
        name_latex = self._identifier_converter.convert(node.name)[0]

        # Arguments
        arg_strs = [self._identifier_converter.convert(arg.arg)[0] for arg in node.args.args]

        latex = self._add_indent("\\begin{algorithmic}\n")
        with self._increment_level():
            latex += self._add_indent(f"\\Function{{{name_latex}}}{{${', '.join(arg_strs)}$}}\n")

            with self._increment_level():
                # Body
                body_strs: list[str] = [self.visit(stmt) for stmt in node.body]
            body_latex = "\n".join(body_strs)

            latex += f"{body_latex}\n"
            latex += self._add_indent("\\EndFunction\n")
        return latex + self._add_indent(r"\end{algorithmic}")

    def visit_If(self, node: ast.If) -> str:
        """Visit an If node."""

        branches = [node]
        while len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
            branches.append(node := node.orelse[0])

        branches_latex = []
        # if and elif statements
        for i, branch in enumerate(branches):
            # test
            cond_latex = self._expression_codegen.visit(branch.test)
            command = r"\If" if i == 0 else r"\ElsIf"
            branches_latex.append(self._add_indent(f"{command}{{${cond_latex}$}}"))

            # body
            with self._increment_level():
                branches_latex.extend(self.visit(stmt) for stmt in branch.body)

        # else
        if node.orelse:
            branches_latex.append(self._add_indent(r"\Else"))
            with self._increment_level():
                branches_latex.extend(self.visit(stmt) for stmt in node.orelse)

        branches_latex.append(self._add_indent(r"\EndIf"))
        return "\n".join(branches_latex)

    def visit_Module(self, node: ast.Module) -> str:
        """Visit a Module node."""
        return self.visit(node.body[0])

    def visit_Return(self, node: ast.Return) -> str:
        """Visit a Return node."""
        return (
            self._add_indent(rf"\State \Return ${self._expression_codegen.visit(node.value)}$")
            if node.value is not None
            else self._add_indent(r"\State \Return")
        )

    def visit_While(self, node: ast.While) -> str:
        """Visit a While node."""
        if node.orelse:
            raise exceptions.LatexifyNotSupportedError("While statement with the else clause is not supported")

        cond_latex = self._expression_codegen.visit(node.test)
        with self._increment_level():
            body_latex = "\n".join(self.visit(stmt) for stmt in node.body)
        return self._add_indent(f"\\While{{${cond_latex}$}}\n") + f"{body_latex}\n" + self._add_indent(r"\EndWhile")

    def visit_Pass(self, _node: ast.Pass) -> str:
        """Visit a Pass node."""
        return self._add_indent(r"\State $\mathbf{pass}$")

    def visit_Break(self, _node: ast.Break) -> str:
        """Visit a Break node."""
        return self._add_indent(r"\State $\mathbf{break}$")

    def visit_Continue(self, _node: ast.Continue) -> str:
        """Visit a Continue node."""
        return self._add_indent(r"\State $\mathbf{continue}$")

    @contextlib.contextmanager
    def _increment_level(self) -> Generator[None, None, None]:
        """Context manager controlling indent level."""
        self._indent_level += 1
        yield
        self._indent_level -= 1

    def _add_indent(self, line: str) -> str:
        """Adds an indent before the line.

        Args:
            line: The line to add an indent to.
        """
        return self._indent_level * self.SPACES_PER_INDENT * " " + line
