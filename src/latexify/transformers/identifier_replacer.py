"""Transformer to replace user symbols."""

from __future__ import annotations

import ast
import keyword

from latexify.analyzers import analyze_attribute
from latexify.ast_utils import make_attribute_nested


class IdentifierReplacer(ast.NodeTransformer):
    """NodeTransformer to replace identifier names.

    This class defines a rule to replace identifiers in AST with the specified new identifiers.
    This runs _before_ the codegen plugins,
    so the plugins will see the modified AST.

    Args:
        mapping: User defined mapping of names. Keys are the original names of the
            identifiers, and corresponding values are the replacements.
            Both keys and values have to represent valid Python identifiers:
            ^[A-Za-z_][A-Za-z0-9_]*$

    Example:
        def foo(bar):
            return baz

        IdentifierReplacer({"foo": "x", "bar": "y", "baz": "z"}) will modify the AST of
        the function above to below:

        def x(y):
            return z
    """

    def __init__(self, mapping: dict[str, str]):
        self._mapping = mapping

        for k, v in mapping.items():
            self._check_valid(k)
            self._check_valid(v)

    def _replace(self, name: str, allow_attribute: bool = False) -> str:
        replaced = self._mapping.get(name, name)
        if not allow_attribute and "." in replaced:
            return name
        return replaced

    def _check_valid(self, name: str) -> None:
        """Check if the name is a valid identifier."""
        if keyword.iskeyword(name) or any(not str.isidentifier(part) for part in name.split(".")):
            raise ValueError(f"'{name}' is not an identifier name.")

    def visit_arg(self, node: ast.arg):
        return ast.arg(
            arg=self._replace(node.arg),
            annotation=node.annotation,
            type_comment=node.type_comment,
        )

    def visit_Name(self, node: ast.Name) -> ast.Name:
        replaced = self._replace(node.id, allow_attribute=True)
        return make_attribute_nested(replaced.split("."))

    def visit_Attribute(self, node: ast.Attribute):
        expanded = ".".join(analyze_attribute(node))
        name = self._replace(expanded, allow_attribute=True)
        return make_attribute_nested(name.split("."))

    def visit_FunctionDef(self, node: ast.FunctionDef):
        replaced = self.generic_visit(node)
        return ast.FunctionDef(
            name=self._replace(node.name),
            args=replaced.args,
            body=replaced.body,
            decorator_list=replaced.decorator_list,
            returns=replaced.returns,
        )
