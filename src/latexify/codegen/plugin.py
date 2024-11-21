from __future__ import annotations

import ast
from abc import ABCMeta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from latexify.codegen.plugin_stack import Stack


class Plugin(ast.NodeVisitor, metaclass=ABCMeta):
    """An element of a linked list of plugins."""

    _base: Stack | None = None

    def _setup(self, stack: Stack) -> None:
        self._base = stack

    def visit(self, node: ast.AST) -> str:
        """Redirects the visit call to the base plugin."""
        return self._base.visit(node)

    def local_visit(self, node: ast.AST) -> str:
        return super().visit(node)

    def generic_visit(self, node):
        # differentiate from actual LatexifyNotSupportedError
        # that gets thrown by the Stack
        raise NotImplementedError

    def visit_and_join(self, items: Iterable[ast.AST], sep: str = ", ") -> str:
        """Visit a list of AST nodes and join the results."""
        return sep.join(map(self.visit, items))


class _ArgumentsPlugin(Plugin):
    def visit_arg(self, node: ast.arg):
        name = self.visit(node.arg)
        if node.annotation:
            arg_type = self.visit(node.annotation)
            return f"{name}: {arg_type}"
        else:
            return name

    def visit_arguments(self, node: ast.arguments) -> str:
        return self.visit_and_join(node.args)
