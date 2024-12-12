from __future__ import annotations

import ast

from latexify.analyzers import analyze_range, reduce_stop_parameter
from latexify.ast_utils import extract_function_name_or_none
from latexify.codegen.plugin import Plugin
from latexify.exceptions import LatexifyError


class SumProdPlugin(Plugin):
    """Converts sum and prod functions to LaTeX."""

    def visit_Call(self, node):
        """Generates sum/prod expression.

        Args:
            node: ast.Call node containing the sum/prod invocation.

        Returns:
            Generated LaTeX, or None if the node has unsupported syntax.
        """
        name = extract_function_name_or_none(node)
        if name not in ("fsum", "sum", "prod") or not node.args or not isinstance(node.args[0], ast.GeneratorExp):
            raise NotImplementedError

        command = {
            "fsum": r"\sum",
            "sum": r"\sum",
            "prod": r"\prod",
        }[name]

        elt, scripts = self._get_sum_prod_info(node.args[0])
        scripts_str = [rf"{command}_{{{lo}}}^{{{up}}}" for lo, up in scripts]
        return " ".join(scripts_str) + rf" \mathopen{{}}\left({{{elt}}}\mathclose{{}}\right)"

    def _get_sum_prod_info(self, node: ast.GeneratorExp) -> tuple[str, list[tuple[str, str]]]:
        r"""Process GeneratorExp for sum and prod functions.

        Args:
            node: GeneratorExp node to be analyzed.

        Returns:
            Tuple of following strings:
                - elt
                - scripts
            which are used to represent sum/prod operators as follows:
                \sum_{scripts[0][0]}^{scripts[0][1]}
                    \sum_{scripts[1][0]}^{scripts[1][1]}
                    ...
                    {elt}

        Raises:
            LateixfyError: Unsupported AST is given.
        """
        elt = self.visit(node.elt)

        scripts: list[tuple[str, str]] = []

        for comp in node.generators:
            range_args = self._get_sum_prod_range(comp)

            if range_args is not None and not comp.ifs:
                target = self.visit(comp.target)
                lower_rhs, upper = range_args
                lower = f"{target} = {lower_rhs}"
            else:
                lower = self.visit(comp)  # Use a usual comprehension form.
                upper = ""

            scripts.append((lower, upper))

        return elt, scripts

    def _get_sum_prod_range(self, node: ast.comprehension) -> tuple[str, str] | None:
        """Helper to process range(...) for sum and prod functions.

        Args:
            node: comprehension node to be analyzed.

        Returns:
            Tuple of following strings:
                - lower_rhs
                - upper
            which are used in _get_sum_prod_info, or None if the analysis failed.
        """
        if not (
            isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name) and node.iter.func.id == "range"
        ):
            return None

        try:
            range_info = analyze_range(node.iter)
        except LatexifyError:
            return None

        if (
            # Only accepts ascending order with step size 1.
            range_info.step_int != 1
            or (
                range_info.start_int is not None
                and range_info.stop_int is not None
                and range_info.start_int >= range_info.stop_int
            )
        ):
            return None

        lower_rhs = self.visit(range_info.start) if range_info.start_int is None else str(range_info.start_int)

        if range_info.stop_int is None:
            upper = self.visit(reduce_stop_parameter(range_info.stop))
        else:
            upper = str(range_info.stop_int - 1)

        return lower_rhs, upper
