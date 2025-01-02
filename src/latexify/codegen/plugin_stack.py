from __future__ import annotations

import ast

from latexify.codegen.expression_codegen import ExpressionVisitor
from latexify.codegen.identifier_converter import IdentifierConverter
from latexify.codegen.plugin import Plugin
from latexify.exceptions import LatexifyNotSupportedError


class Stack(ast.NodeVisitor):
    _plugins: tuple[Plugin]

    def __init__(self, *plugins: Plugin):
        self._plugins = plugins
        for plugin in plugins:
            if not isinstance(plugin, Plugin):
                raise TypeError(f"Expected Plugin, got {type(plugin)}")
            plugin._setup(self)  # noqa: SLF001

    def visit(self, node: ast.AST) -> str:
        """Apply the plugins to the AST node.

        Args:
            node (ast.AST): The AST node to convert to LaTeX.

        Raises:
            LatexifyNotSupportedError: If the AST node is not supported by any plugin.

        Returns:
            str: The LaTeX code.
        """
        for plugin in self._plugins:
            try:
                return ast.NodeVisitor.visit(plugin, node)
            except NotImplementedError:
                pass

        raise LatexifyNotSupportedError(f"Unsupported AST: {node.__class__.__name__}")


def _default_stack(
    *plugins: Plugin,
    use_set_symbols: bool = False,
    use_math_symbols: bool = False,
    use_mathrm: bool = True,
    id_to_latex: dict[str, str] | None = None,
) -> Stack:
    """Append the default core plugins to the given plugins."""

    return Stack(
        *plugins,
        ExpressionVisitor(use_set_symbols=use_set_symbols),
        IdentifierConverter(
            use_math_symbols=use_math_symbols,
            use_mathrm=use_mathrm,
            id_to_latex=id_to_latex,
        ),
    )
