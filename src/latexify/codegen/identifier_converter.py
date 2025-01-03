from __future__ import annotations

from typing import TYPE_CHECKING

from latexify.analyzers import analyze_attribute
from latexify.codegen.plugin import Plugin

if TYPE_CHECKING:
    import ast


class IdentifierConverter(Plugin):
    """Converts Python identifiers to LaTeX expressions.

    Args:
        use_math_symbols (bool, optional): Whether to convert "math symbol" identifiers
            (e.g., "alpha") to the corresponding LaTeX symbol (e.g., "\\alpha"). Defaults to False.
        use_mathrm (bool, optional): Whether to wrap identifiers in \\mathrm{}. Defaults to True.
        custom_identifiers (dict[str, str], optional): A dictionary mapping Python identifiers to LaTeX expressions.
            These custom mappings take precedence over the other options. Defaults to None.
    """

    def __init__(
        self,
        use_math_symbols: bool = False,
        use_mathrm: bool = True,
        id_to_latex: dict[str, str] | None = None,
    ):
        self._use_math_symbols = use_math_symbols
        self._use_mathrm = use_mathrm
        self._id_to_latex = id_to_latex or {}

    def visit_str(self, name: str) -> str:
        """Treat raw strings passed to `visit` as identifiers.

        This enables customization of identifier conversion.
        """
        return self.convert_identifier(name)[0]

    def visit_Name(self, node: ast.Name) -> str:
        """Converts a root identifier to LaTeX."""
        return self.convert_identifier(node.id)[0]

    def visit_Attribute(self, node: ast.Attribute):
        parts = analyze_attribute(node)
        name = ".".join(parts)
        if name in self._id_to_latex:
            return self._id_to_latex[name]
        return self.visit_and_join(parts, ".")

    def convert_identifier(self, name: str) -> str:
        """Converts Python identifiers (e.g. variable names) to appropriate LaTeX expression."""
        if name in self._id_to_latex:
            return self._id_to_latex[name], False

        if self._use_math_symbols and name in MATH_SYMBOLS:
            return "\\" + name, True

        if len(name) == 1 and name != "_":
            return name, True

        parts = name.split("_")
        if (
            self._use_math_symbols
            and len(parts) == 2
            and (parts[0] in MATH_SYMBOLS or len(parts[0]) == 1)
            and parts[1] != ""
        ):
            first = ("" if len(parts[0]) == 1 else "\\") + parts[0]
            if parts[1] == "hat":
                return r"\widehat{" + first + r"}", False
            return first + r"_{\mathrm{" + parts[1] + r"}}", False

        escaped = name.replace("_", r"\_")

        return r"\mathrm{" + escaped + r"}" if self._use_mathrm else escaped, False


MATH_SYMBOLS = {
    "aleph",
    "alpha",
    "beta",
    "beth",
    "chi",
    "daleth",
    "delta",
    "digamma",
    "epsilon",
    "eta",
    "gamma",
    "gimel",
    "hbar",
    "infty",
    "iota",
    "kappa",
    "lambda",
    "mu",
    "nabla",
    "nu",
    "omega",
    "phi",
    "pi",
    "psi",
    "rho",
    "sigma",
    "tau",
    "theta",
    "upsilon",
    "varepsilon",
    "varkappa",
    "varphi",
    "varpi",
    "varrho",
    "varsigma",
    "vartheta",
    "xi",
    "zeta",
    "Delta",
    "Gamma",
    "Lambda",
    "Omega",
    "Phi",
    "Pi",
    "Psi",
    "Sigma",
    "Theta",
    "Upsilon",
    "Xi",
}
