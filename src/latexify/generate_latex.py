"""Generate LaTeX code."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Any

from latexify import ast_utils, codegen, transformers

if TYPE_CHECKING:
    from collections.abc import Callable


class Style(enum.Enum):
    """The style of the generated LaTeX."""

    ALGORITHMIC = "algorithmic"
    FUNCTION = "function"
    IPYTHON_ALGORITHMIC = "ipython-algorithmic"


def get_latex(
    fn: Callable[..., Any],
    *,
    style: Style = Style.FUNCTION,
    expand_functions: set[str] | None = None,
    identifiers: dict[str, str] | None = None,
    prefixes: set[str] | None = None,
    reduce_assignments: bool = False,
    use_math_symbols: bool = False,
    use_set_symbols: bool = False,
    use_signature: bool = True,
) -> str:
    """Obtains LaTeX description from the function's source.

    Args:
        fn: Reference to a function to analyze.
        style: Style of the LaTeX description, the default is FUNCTION.
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

    Returns:
        Generated LaTeX description.

    Raises:
        latexify.exceptions.LatexifyError: Something went wrong during conversion.
    """
    # Obtains the source AST.
    tree = ast_utils.parse_function(fn)

    # Mandatory AST transformations
    tree = transformers.AugAssignReplacer().visit(tree)

    # Conditional AST transformations
    if prefixes is not None:
        tree = transformers.PrefixTrimmer(prefixes).visit(tree)
    if identifiers is not None:
        tree = transformers.IdentifierReplacer(identifiers).visit(tree)
    if reduce_assignments:
        tree = transformers.DocstringRemover().visit(tree)
        tree = transformers.AssignmentReducer().visit(tree)
    if expand_functions is not None:
        tree = transformers.FunctionExpander(expand_functions).visit(tree)

    # Generates LaTeX.
    if style == Style.ALGORITHMIC:
        return codegen.AlgorithmicCodegen(
            use_math_symbols=use_math_symbols,
            use_set_symbols=use_set_symbols,
        ).visit(tree)
    elif style == Style.FUNCTION:
        return codegen.FunctionCodegen(
            use_math_symbols=use_math_symbols,
            use_signature=use_signature,
            use_set_symbols=use_set_symbols,
        ).visit(tree)
    elif style == Style.IPYTHON_ALGORITHMIC:
        return codegen.IPythonAlgorithmicCodegen(
            use_math_symbols=use_math_symbols,
            use_set_symbols=use_set_symbols,
        ).visit(tree)

    raise ValueError(f"Unrecognized style: {style}")
