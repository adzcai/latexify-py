"""Codegen for single algorithms."""

from __future__ import annotations

import ast
import contextlib
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING

from latexify.codegen.plugin import _ArgumentsPlugin
from latexify.exceptions import LatexifyNotSupportedError

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable


class _AlgorithmCodegenBase(_ArgumentsPlugin, metaclass=ABCMeta):
    """Codegen for single algorithms.

    This subclasses the ast.NodeVisitor
    to take in an AST rooted at a single FunctionDef node
    and generate LaTeX `algpseudocode` code for the algorithm.

    If `ipython` is enabled,
    doesn't use the `algorithmic` environment.

    This codegen works for Module with single FunctionDef node to generate a single
    LaTeX expression of the given algorithm.
    """

    _indent_level: int = 0
    LINE_BREAK: str  # Line break character

    @abstractmethod
    def _statement(self, line: str) -> str:
        """Add a statement to the algorithm."""

    def visit_Assign(self, node: ast.Assign) -> str:
        """Visit an Assign node."""
        return self._statement(self.visit_and_join([*node.targets, node.value], r" \gets "))

    def visit_Expr(self, node: ast.Expr) -> str:
        """Visit an Expr node."""
        return self._statement(self.visit(node.value))

    def visit_For(self, node: ast.For) -> str:
        """Visit a For node."""
        if len(node.orelse) != 0:
            raise LatexifyNotSupportedError("For statement with the else clause is not supported")

        target_latex, iter_latex = self.visit(node.target), self.visit(node.iter)
        block = IndentedBlock(self)
        block.add(self._begin_for(target_latex, iter_latex))
        with self._increment_level():
            block.add(node.body)
        block.add(self._end_for())
        return str(block)

    @abstractmethod
    def _begin_for(self, target_latex: str, iter_latex: str) -> str:
        """Begin a For loop."""

    @abstractmethod
    def _end_for(self) -> str:
        """End a For loop."""

    def visit_FunctionDef(self, node: ast.FunctionDef) -> str:
        """Visit a FunctionDef node."""
        name_latex, args_latex = node.name, self.visit(node.args)
        top = self._indent_level == 0
        block = IndentedBlock(self)
        block.add(self._begin_function(name_latex, args_latex, top))
        with self._increment_level():
            block.add(node.body)
        block.add(self._end_function(top))
        return str(block)

    @abstractmethod
    def _begin_function(self, name_latex: str, arg_latex: str, top: bool) -> str:
        """Begin a function definition."""

    @abstractmethod
    def _end_function(self, top: bool) -> str:
        """End a function definition."""

    def visit_If(self, node: ast.If) -> str:
        """Visit an If node."""

        branches = [node]
        while len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
            branches.append(node := node.orelse[0])

        block = IndentedBlock(self)
        # if and elif statements
        for i, branch in enumerate(branches):
            # test
            cond_latex = self.visit(branch.test)
            command = self._if(cond_latex) if i == 0 else self._elif(cond_latex)
            block.add(command)

            # body
            with self._increment_level():
                block.add(branch.body)

        # else
        if node.orelse:
            block.add(self._else())
            with self._increment_level():
                block.add(node.orelse)

        block.add(self._end_if())
        return str(block)

    @abstractmethod
    def _if(self, cond_latex: str) -> str:
        """If statement."""

    @abstractmethod
    def _elif(self, cond_latex: str) -> str:
        """Elif statement."""

    @abstractmethod
    def _else(self) -> str:
        """Else statement."""

    @abstractmethod
    def _end_if(self) -> str:
        """End if statement."""

    def visit_Module(self, node: ast.Module) -> str:
        """Visit a Module node."""
        return self.visit(node.body[0])

    def visit_Return(self, node: ast.Return) -> str:
        """Visit a Return node."""
        value = self.visit(node.value) if node.value is not None else None
        return self.add_indent(self._return(value))

    @abstractmethod
    def _return(self, value_latex: str | None) -> str:
        """Return statement."""

    def visit_While(self, node: ast.While) -> str:
        """Visit a While node."""
        if node.orelse:
            raise LatexifyNotSupportedError("While statement with the else clause is not supported")
        block = IndentedBlock(self)
        block.add(self._begin_while(self.visit(node.test)))
        with self._increment_level():
            block.add(node.body)
        block.add(self._end_while())
        return str(block)

    @abstractmethod
    def _begin_while(self, cond_latex: str) -> str:
        """Begin a While loop."""

    @abstractmethod
    def _end_while(self) -> str:
        """End a While loop."""

    def visit_Pass(self, _node: ast.Pass) -> str:
        """Visit a Pass node."""
        return self._statement(r"\mathbf{pass}")

    def visit_Break(self, _node: ast.Break) -> str:
        """Visit a Break node."""
        return self._statement(r"\mathbf{break}")

    def visit_Continue(self, _node: ast.Continue) -> str:
        """Visit a Continue node."""
        return self._statement(r"\mathbf{continue}")

    @contextlib.contextmanager
    def _increment_level(self) -> Generator[None, None, None]:
        """Context manager controlling indent level."""
        self._indent_level += 1
        yield
        self._indent_level -= 1

    @abstractmethod
    def add_indent(self, line: str) -> str:
        """Adds an indent before the line.

        Args:
            line: The line to add an indent to.
        """


class AlgorithmicCodegen(_AlgorithmCodegenBase):
    SPACES_PER_INDENT = 4
    LINE_BREAK = "\n"

    def _statement(self, line):
        return self.add_indent(rf"\State ${line}$")

    def _begin_for(self, target_latex, iter_latex):
        return f"\\For{{${target_latex} \\in {iter_latex}$}}"

    def _end_for(self):
        return r"\EndFor"

    def _if(self, cond_latex: str):
        return r"\If{$" + cond_latex + r"$}"

    def _elif(self, cond_latex: str):
        return r"\ElsIf{$" + cond_latex + r"$}"

    def _else(self):
        return r"\Else"

    def _begin_function(self, name_latex: str, arg_latex: str, top: bool):
        if top:
            yield r"\begin{algorithmic}"
        self._indent_level += 1
        yield r"\Function{" + name_latex + r"}{$" + arg_latex + r"$}"

    def _end_function(self, top):
        yield r"\EndFunction"
        self._indent_level -= 1
        if top:
            yield r"\end{algorithmic}"

    def _end_if(self):
        return r"\EndIf"

    def _begin_while(self, cond_latex: str):
        return r"\While{$" + cond_latex + r"$}"

    def _end_while(self):
        return r"\EndWhile"

    def _return(self, value_latex):
        return r"\State \Return " + f"${value_latex}$" if value_latex is not None else r"\State \Return"

    def add_indent(self, line):
        return self._indent_level * self.SPACES_PER_INDENT * " " + line


class IPythonLatexifier(_AlgorithmCodegenBase):
    EM_PER_INDENT = 1
    LINE_BREAK = r" \\ "

    def _statement(self, line):
        return self.add_indent(line)

    def _begin_for(self, target_latex: str, iter_latex: str):
        return r"\mathbf{for} \ " + target_latex + r" \in " + iter_latex + r" \ \mathbf{do}"

    def _end_for(self):
        return r"\mathbf{end \ for}"

    def _if(self, cond_latex: str):
        return r"\mathbf{if} \ " + cond_latex

    def _elif(self, cond_latex: str):
        return r"\mathbf{else if} \ " + cond_latex

    def _else(self):
        return r"\mathbf{else}"

    def _begin_function(self, name_latex: str, arg_latex: str, top: bool):
        s = r"\begin{array}{l} " if top else ""
        return s + r"\mathbf{function} \ " + f"{self.visit(name_latex)}({arg_latex})"

    def _end_function(self, top):
        s = r"\mathbf{end \ function}"
        return s + r" \end{array}" if top else s

    def _end_if(self):
        return r"\mathbf{end \ if}"

    def _begin_while(self, cond_latex):
        return r"\mathbf{while} \ " + cond_latex

    def _end_while(self):
        return r"\mathbf{end \ while}"

    def _return(self, value_latex: str | None):
        return r"\mathbf{return} \ " + value_latex if value_latex is not None else r"\mathbf{return}"

    def add_indent(self, line):
        return rf"\hspace{{{self._indent_level * self.EM_PER_INDENT}em}} {line}" if self._indent_level > 0 else line


class IndentedBlock:
    _items: list[str]
    _visitor: AlgorithmicCodegen

    def __init__(self, visitor) -> None:
        self._items = []
        self._visitor = visitor

    def add(self, item: str | ast.AST | Iterable[str | ast.AST]) -> None:
        if isinstance(item, (ast.AST, str)):
            latex = self._visitor.add_indent(item) if isinstance(item, str) else self._visitor.visit(item)
            self._items.append(latex)
        else:
            for sub_item in item:
                self.add(sub_item)

    def __str__(self) -> str:
        return self._visitor.LINE_BREAK.join(self._items)
