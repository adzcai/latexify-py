"""Codegen for single functions."""

from __future__ import annotations

import ast
import sys

from latexify import ast_utils, exceptions
from latexify.codegen import expression_codegen
from latexify.codegen.plugin import _ArgumentsPlugin


class FunctionCodegen(_ArgumentsPlugin):
    """Codegen for single functions.

    This codegen translates a single FunctionDef node to a corresponding LaTeX expression.

    Args:
        use_signature: Whether to add the function signature (e.g. `f(x) = ...`)
            before the expression or not.
    """

    _use_signature: bool

    def __init__(
        self,
        *,
        use_signature: bool = True,
    ) -> None:
        self._use_signature = use_signature

    def wrap_ipython(self, latex: str) -> str:
        return f"$$ {latex} $$"

    def visit_Module(self, node: ast.Module) -> str:
        """Visit a Module node."""
        return self.visit(node.body[0])

    def visit_FunctionDef(self, node: ast.FunctionDef) -> str:
        """Visit a FunctionDef node."""
        # Function name
        name_str = self.visit(node.name)

        body_strs: list[str] = []

        # Assignment statements (if any): x = ...
        for child in node.body[:-1]:
            if isinstance(child, ast.Expr) and ast_utils.is_constant(child.value):
                continue

            if not isinstance(child, ast.Assign):
                raise exceptions.LatexifyNotSupportedError(
                    "Codegen supports only Assign nodes in multiline functions, " f"but got: {type(child).__name__}"
                )
            body_strs.append(self.visit(child))

        return_stmt = node.body[-1]

        if sys.version_info >= (3, 10):
            if not isinstance(return_stmt, (ast.Return, ast.If, ast.Match)):
                raise exceptions.LatexifySyntaxError(f"Unsupported last statement: {type(return_stmt).__name__}")
        elif not isinstance(return_stmt, (ast.Return, ast.If)):
            raise exceptions.LatexifySyntaxError(f"Unsupported last statement: {type(return_stmt).__name__}")

        # Function definition: f(x, ...) \triangleq ...
        return_str = self.visit(return_stmt)
        if self._use_signature:
            # Function signature: f(x, ...)
            signature_str = name_str + "(" + self.visit(node.args) + ")"
            return_str = signature_str + " = " + return_str

        if not body_strs:
            # Only the definition.
            return return_str

        # Definition with several assignments. Wrap all statements with array.
        body_strs.append(return_str)
        return r"\begin{array}{l} " + r" \\ ".join(body_strs) + r" \end{array}"

    def visit_Assign(self, node: ast.Assign) -> str:
        """Visit an Assign node."""
        operands: list[str] = [self.visit(t) for t in node.targets]
        operands.append(self.visit(node.value))
        return " = ".join(operands)

    def visit_Return(self, node: ast.Return) -> str:
        """Visit a Return node."""
        return self.visit(node.value) if node.value is not None else expression_codegen.convert_constant(None)

    def visit_If(self, node: ast.If) -> str:
        """Visit an If node."""
        latex = r"\left\{ \begin{array}{ll} "

        current_stmt: ast.stmt = node

        while isinstance(current_stmt, ast.If):
            if len(current_stmt.body) != 1 or len(current_stmt.orelse) != 1:
                raise exceptions.LatexifySyntaxError("Multiple statements are not supported in If nodes.")

            cond_latex = self.visit(current_stmt.test)
            true_latex = self.visit(current_stmt.body[0])
            latex += true_latex + r", & \mathrm{if} \ " + cond_latex + r" \\ "
            current_stmt = current_stmt.orelse[0]

        latex += self.visit(current_stmt)
        return latex + r", & \mathrm{otherwise} \end{array} \right."

    def visit_Match(self, node: ast.Match) -> str:
        """Visit a Match node"""
        if not (
            len(node.cases) >= 2
            and isinstance(node.cases[-1].pattern, ast.MatchAs)
            and node.cases[-1].pattern.name is None
        ):
            raise exceptions.LatexifySyntaxError("Match statement must contain the wildcard.")

        subject_latex = self.visit(node.subject)
        case_latexes: list[str] = []

        for i, case in enumerate(node.cases):
            if len(case.body) != 1 or not isinstance(case.body[0], ast.Return):
                raise exceptions.LatexifyNotSupportedError("Match cases must contain exactly 1 return statement.")

            if i < len(node.cases) - 1:
                body_latex = self.visit(case.body[0])
                cond_latex = self.visit(case.pattern)
                case_latexes.append(body_latex + r", & \mathrm{if} \ " + subject_latex + cond_latex)
            else:
                case_latexes.append(self.visit(node.cases[-1].body[0]) + r", & \mathrm{otherwise}")

        return r"\left\{ \begin{array}{ll} " + r" \\ ".join(case_latexes) + r" \end{array} \right."

    def visit_MatchValue(self, node: ast.MatchValue) -> str:
        """Visit a MatchValue node"""
        latex = self.visit(node.value)
        return " = " + latex
