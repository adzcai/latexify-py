from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from latexify.ast_utils import parse_function
from latexify.codegen.function_codegen import FunctionCodegen
from latexify.codegen.plugin_stack import _default_stack
from latexify.transformers.assignment_reducer import AssignmentReducer
from latexify.transformers.aug_assign_replacer import AugAssignReplacer
from latexify.transformers.docstring_remover import DocstringRemover
from latexify.transformers.function_expander import FunctionExpander
from latexify.transformers.identifier_replacer import IdentifierReplacer
from latexify.transformers.prefix_trimmer import PrefixTrimmer

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from latexify.codegen.plugin import Plugin


def get_latex(
    fn: Callable[..., Any],
    /,
    base_plugin: Plugin | None = None,
    to_file: str | None = None,
    # transformers arguments
    trim_prefixes: set[str] | None = None,
    replace_identifiers: dict[str, str] | None = None,
    reduce_assignments: bool = False,
    expand_functions: set[str] | None = None,
    # builtin plugin arguments
    use_set_symbols: bool = False,
    use_math_symbols: bool = False,
    use_mathrm: bool = True,
    id_to_latex: dict[str, str] | None = None,
    plugins: Sequence[Plugin] | None = None,
    use_signature: bool = True,
) -> str:
    """Generate LaTeX code for the given function."""

    tree = parse_function(fn)

    transformers = [
        t
        for t in [
            AugAssignReplacer(),
            trim_prefixes and PrefixTrimmer(trim_prefixes),
            replace_identifiers and IdentifierReplacer(replace_identifiers),
            reduce_assignments and DocstringRemover(),
            reduce_assignments and AssignmentReducer(),
            expand_functions and FunctionExpander(expand_functions),
        ]
        if t
    ]

    for transformer in transformers:
        tree = transformer.visit(tree)

    stack = _default_stack(
        *(plugins or []),
        base_plugin or FunctionCodegen(use_signature=use_signature),
        use_set_symbols=use_set_symbols,
        use_math_symbols=use_math_symbols,
        use_mathrm=use_mathrm,
        id_to_latex=id_to_latex,
    )
    latex = stack.visit(tree)

    if to_file and isinstance(latex, str):
        path = Path(to_file) if isinstance(to_file, str) else Path(f"{fn.__name__}.tex")
        if path.is_dir():
            path = path / f"{fn.__name__}.tex"
        path.write_text(latex)

    return latex
