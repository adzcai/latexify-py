from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from latexify.analyzers import extract_function_name_or_none, extract_int_or_none
from latexify.codegen.plugin import Plugin

if TYPE_CHECKING:
    from collections.abc import Callable


class NumpyPlugin(Plugin):
    """Converts numpy linear algebra expressions to LaTeX.

    Args:
        pinv_symbol (str, optional): The symbol to use for matrix pseudoinverses. Defaults to `\\dagger`.
    """

    def __init__(
        self,
        pinv_symbol: str = r"\dagger",
    ):
        self.CUSTOM_FUNCTIONS: dict[str, Callable[[ast.NodeVisitor, ast.Call], str]] = {
            "array": self._generate_matrix,
            "ndarray": self._generate_matrix,
            "zeros": self._generate_zeros,
            "identity": self._generate_identity,
            "transpose": self._generate_transpose,
            "det": self._generate_determinant,
            "matrix_rank": self._generate_matrix_rank,
            "matrix_power": self._generate_matrix_power,
            "inv": self._generate_inv,
            "pinv": self._generate_pinv,
            "grad": self._generate_grad,
        }
        self._pinv_symbol = pinv_symbol

    def visit_Call(self, node):
        func_name = extract_function_name_or_none(node)

        if func_name in self.CUSTOM_FUNCTIONS and (out := self.CUSTOM_FUNCTIONS[func_name](node)) is not None:
            return out

        return self.generic_visit(node)

    def _generate_matrix(self, node: ast.Call) -> str | None:
        """Generates matrix expression.

        Args:
            node: ast.Call node containing the ndarray invocation.

        Returns:
            Generated LaTeX, or None if the node has unsupported syntax.
        """

        def generate_matrix_from_array(data: list[list[str]]) -> str:
            """Helper to generate a bmatrix environment."""
            contents = r" \\ ".join(" & ".join(row) for row in data)
            return r"\begin{bmatrix} " + contents + r" \end{bmatrix}"

        arg = node.args[0]
        if not isinstance(arg, ast.List) or not arg.elts:
            # Not an array or no rows
            return None

        row0 = arg.elts[0]

        if not isinstance(row0, ast.List):
            # Maybe 1 x N array
            return generate_matrix_from_array([[self.visit(x) for x in arg.elts]])

        if not row0.elts:
            # No columns
            return None

        ncols = len(row0.elts)

        rows: list[list[str]] = []

        for row in arg.elts:
            if not isinstance(row, ast.List) or len(row.elts) != ncols:
                # Length mismatch
                return None

            rows.append([self.visit(x) for x in row.elts])

        return generate_matrix_from_array(rows)

    def _generate_zeros(self, node: ast.Call) -> str | None:
        """Generates LaTeX for numpy.zeros.
        Args:
            node: ast.Call node containing the appropriate method invocation.
        Returns:
            Generated LaTeX, or None if the node has unsupported syntax.
        """
        name = extract_function_name_or_none(node)
        assert name == "zeros", name

        if len(node.args) != 1:
            return None

        # All args to np.zeros should be numeric.
        if isinstance(node.args[0], ast.Tuple):
            dims = [extract_int_or_none(x) for x in node.args[0].elts]
            if any(x is None for x in dims):
                return None
            if not dims:
                return "0"
            if len(dims) == 1:
                dims = [1, dims[0]]

            dims_latex = r" \times ".join(str(x) for x in dims)
        else:
            dim = extract_int_or_none(node.args[0])
            if not isinstance(dim, int):
                return None
            # 1 x N array of zeros
            dims_latex = rf"1 \times {dim}"

        return rf"\mathbf{{0}}^{{{dims_latex}}}"

    def _generate_identity(self, node: ast.Call) -> str | None:
        """Generates LaTeX for numpy.identity.
        Args:
            node: ast.Call node containing the appropriate method invocation.
        Returns:
            Generated LaTeX, or None if the node has unsupported syntax.
        """
        name = extract_function_name_or_none(node)
        assert name == "identity", name

        if len(node.args) != 1:
            return None

        ndims = extract_int_or_none(node.args[0])
        if ndims is None:
            return None

        return rf"\mathbf{{I}}_{{{ndims}}}"

    def _generate_transpose(self, node: ast.Call) -> str | None:
        """Generates LaTeX for numpy.transpose.
        Args:
            node: ast.Call node containing the appropriate method invocation.
        Returns:
            Generated LaTeX, or None if the node has unsupported syntax.
        Raises:
            LatexifyError: Unsupported argument type given.
        """
        name = extract_function_name_or_none(node)
        assert name == "transpose", name

        if len(node.args) != 1:
            return None

        func_arg = node.args[0]
        if isinstance(func_arg, ast.Name):
            return rf"\mathbf{{{func_arg.id}}}^\intercal"
        else:
            return None

    def _generate_determinant(self, node: ast.Call) -> str | None:
        """Generates LaTeX for numpy.linalg.det.
        Args:
            node: ast.Call node containing the appropriate method invocation.
        Returns:
            Generated LaTeX, or None if the node has unsupported syntax.
        Raises:
            LatexifyError: Unsupported argument type given.
        """
        name = extract_function_name_or_none(node)
        assert name == "det", name

        if len(node.args) != 1:
            return None

        func_arg = node.args[0]
        if isinstance(func_arg, ast.Name):
            arg_id = rf"\mathbf{{{func_arg.id}}}"
            return rf"\det \mathopen{{}}\left( {arg_id} \mathclose{{}}\right)"
        elif isinstance(func_arg, ast.List):
            matrix = self._generate_matrix(node)
            return rf"\det \mathopen{{}}\left( {matrix} \mathclose{{}}\right)"

        return None

    def _generate_matrix_rank(self, node: ast.Call) -> str | None:
        """Generates LaTeX for numpy.linalg.matrix_rank.
        Args:
            node: ast.Call node containing the appropriate method invocation.
        Returns:
            Generated LaTeX, or None if the node has unsupported syntax.
        Raises:
            LatexifyError: Unsupported argument type given.
        """
        name = extract_function_name_or_none(node)
        assert name == "matrix_rank", name

        if len(node.args) != 1:
            return None

        func_arg = node.args[0]
        if isinstance(func_arg, ast.Name):
            arg_id = rf"\mathbf{{{func_arg.id}}}"
            return rf"\mathrm{{rank}} \mathopen{{}}\left( {arg_id} \mathclose{{}}\right)"
        elif isinstance(func_arg, ast.List):
            matrix = self._generate_matrix(node)
            return rf"\mathrm{{rank}} \mathopen{{}}\left( {matrix} \mathclose{{}}\right)"

        return None

    def _generate_matrix_power(self, node: ast.Call) -> str | None:
        """Generates LaTeX for numpy.linalg.matrix_power.
        Args:
            node: ast.Call node containing the appropriate method invocation.
        Returns:
            Generated LaTeX, or None if the node has unsupported syntax.
        Raises:
            LatexifyError: Unsupported argument type given.
        """
        name = extract_function_name_or_none(node)
        assert name == "matrix_power", name

        if len(node.args) != 2:
            return None

        func_arg = node.args[0]
        power_arg = node.args[1]
        if isinstance(power_arg, ast.Num):
            if isinstance(func_arg, ast.Name):
                return rf"\mathbf{{{func_arg.id}}}^{{{power_arg.n}}}"
            elif isinstance(func_arg, ast.List):
                matrix = self._generate_matrix(node)
                if matrix is not None:
                    return rf"{matrix}^{{{power_arg.n}}}"
        return None

    def _generate_inv(self, node: ast.Call) -> str | None:
        """Generates LaTeX for numpy.linalg.inv.
        Args:
            node: ast.Call node containing the appropriate method invocation.
        Returns:
            Generated LaTeX, or None if the node has unsupported syntax.
        Raises:
            LatexifyError: Unsupported argument type given.
        """
        name = extract_function_name_or_none(node)
        assert name == "inv", name

        if len(node.args) != 1:
            return None

        func_arg = node.args[0]
        if isinstance(func_arg, ast.Name):
            return rf"\mathbf{{{func_arg.id}}}^{{-1}}"
        elif isinstance(func_arg, ast.List):
            return rf"{self._generate_matrix(node)}^{{-1}}"
        return None

    def _generate_pinv(self, node: ast.Call) -> str | None:
        """Generates LaTeX for numpy.linalg.pinv.
        Args:
            node: ast.Call node containing the appropriate method invocation.
        Returns:
            Generated LaTeX, or None if the node has unsupported syntax.
        Raises:
            LatexifyError: Unsupported argument type given.
        """
        name = extract_function_name_or_none(node)
        assert name == "pinv", name

        if len(node.args) != 1:
            return None

        func_arg = node.args[0]
        if isinstance(func_arg, ast.Name):
            return r"\mathbf{" + func_arg.id + r"}^{" + self._pinv_symbol + r"}"
        elif isinstance(func_arg, ast.List):
            return self._generate_matrix(node) + r"^{" + self._pinv_symbol + r"}"
        return None

    def _generate_grad(self, node: ast.Call) -> str | None:
        return r"\nabla \mathopen{}\left(" + self.visit(node.args[0]) + r"\mathclose{}\right)"
