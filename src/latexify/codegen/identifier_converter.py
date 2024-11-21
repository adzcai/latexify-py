from __future__ import annotations

from latexify.codegen.plugin import Plugin


class IdentifierConverter(Plugin):
    """Converts Python identifiers to LaTeX expressions.

    Args:
        use_math_symbols (bool): Whether to convert identifiers with a math symbol
            surface (e.g., "alpha") to the LaTeX symbol (e.g., "\\alpha").
        use_mathrm (bool): Whether to wrap identifiers in \\mathrm{}.
    """

    def __init__(
        self,
        use_math_symbols: bool | None = None,
        use_mathrm: bool | None = None,
    ):
        self._use_math_symbols = False if use_math_symbols is None else use_math_symbols
        self._use_mathrm = True if use_mathrm is None else use_mathrm

    def visit_str(self, name: str) -> str:
        return self.convert_identifier(name)[0]

    def convert_identifier(self, name: str) -> str:
        r"""Converts Python identifiers (e.g. variable names) to appropriate LaTeX expression."""
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
