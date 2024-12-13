import ast

from latexify.codegen.plugin import Plugin


class JaxTypingPlugin(Plugin):
    def visit_Subscript(self, node: ast.Subscript):
        if (
            isinstance(node.value, ast.Name)
            and node.value.id in ("Float", "Int")
            and isinstance(node.slice, ast.Tuple)
            and len(elts := node.slice.elts) == 2
            and isinstance(elts[0], ast.Name)
            and elts[0].id == "Array"
            and isinstance(elts[1], ast.Constant)
            and isinstance(dim := elts[1].value, str)
        ):
            dim = r" \times ".join(dim.strip().split())
            return r"\mathbb{R}^{" + dim + r"}"
        raise NotImplementedError
