"""Definition of the Config class."""

from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class Config:
    """Configurations to control the behavior of latexify.

    Attributes:
        expand_functions: If set, the names of the functions to expand.
        identifiers: If set, the mapping to replace identifier names in the
            function. Keys are the original names of the identifiers,
            and corresponding values are the replacements.
            Both keys and values have to represent valid Python identifiers:
            ^[A-Za-z_][A-Za-z0-9_]*$
        prefixes: Prefixes of identifiers to trim. E.g., if "foo.bar" in prefixes, all
            identifiers with the form "foo.bar.suffix" will be replaced to "suffix"
        reduce_assignments: If True, assignment statements are used to synthesize
            the final expression.
        use_math_symbols: Whether to convert identifiers with a math symbol surface
            (e.g., "alpha") to the LaTeX symbol (e.g., "\\alpha").
        use_set_symbols: Whether to use set symbols or not.
        use_signature: Whether to add the function signature before the expression
            or not.
    """

    expand_functions: set[str] | None = None
    identifiers: dict[str, str] | None = None
    prefixes: set[str] | None = None
    reduce_assignments: bool = False
    use_math_symbols: bool = False
    use_set_symbols: bool = False
    use_signature: bool = True
