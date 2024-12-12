from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from latexify.ast_utils import parse_function
from latexify.codegen.function_codegen import FunctionCodegen
from latexify.codegen.plugin_stack import default_stack
from latexify.transformers.assignment_reducer import AssignmentReducer
from latexify.transformers.aug_assign_replacer import AugAssignReplacer
from latexify.transformers.docstring_remover import DocstringRemover
from latexify.transformers.function_expander import FunctionExpander
from latexify.transformers.identifier_replacer import IdentifierReplacer
from latexify.transformers.prefix_trimmer import PrefixTrimmer

if TYPE_CHECKING:
    import ast
    from collections.abc import Callable, Generator, Iterable

    from latexify.codegen.plugin import Plugin


def default_transformers(
    prefixes: set[str] | None = None,
    identifiers: dict[str, str] | None = None,
    reduce_assignments: bool = False,
    expand_functions: set[str] | None = None,
) -> Generator[ast.NodeTransformer, None, None]:
    """
    Get a generator of transformers to apply to the AST.

    Args:
        prefixes: Prefixes of identifiers to trim. e.g. if set to ["foo.bar"], all
            identifiers of the form "foo.bar.suffix" will be replaced with "suffix"
        identifiers: If set, the mapping to replace identifier names in the
            function. Keys are the original names of the identifiers,
            and corresponding values are the replacements.
            Both keys and values have to represent valid Python identifiers:
            ^[A-Za-z_][A-Za-z0-9_]*$
        reduce_assignments: If True, assignment statements are used to synthesize
            the final expression.
        expand_functions: If set, the names of the functions to expand.
    """
    return [
        t
        for t in [
            AugAssignReplacer(),
            prefixes and PrefixTrimmer(prefixes),
            identifiers and IdentifierReplacer(identifiers),
            reduce_assignments and DocstringRemover(),
            reduce_assignments and AssignmentReducer(),
            expand_functions and FunctionExpander(expand_functions),
        ]
        if t
    ]


def get_latex(
    fn: Callable[..., Any],
    /,
    LatexifierClass: type[Plugin] = FunctionCodegen,  # noqa: N803
    to_file: str | None = None,
    # transformers arguments
    prefixes: set[str] | None = None,
    replace_identifiers: dict[str, str] | None = None,
    reduce_assignments: bool = False,
    expand_functions: set[str] | None = None,
    pre_transformers: Iterable[ast.NodeTransformer] | None = None,
    post_transformers: Iterable[ast.NodeTransformer] | None = None,
    # builtin plugin arguments
    use_set_symbols: bool | None = None,
    use_math_symbols: bool | None = None,
    use_mathrm: bool | None = None,
    custom_identifiers: dict[str, str] | None = None,
    # custom plugins
    plugins: Iterable[Plugin] | None = None,
    **kwargs: Any,
) -> str:
    """Convert a function to LaTeX code.

    Args:
        fn (Callable[..., Any]): The function to convert.
        LatexifierClass (type[Plugin], optional): The base plugin class to use for conversion. Defaults to FunctionCodegen.
        prefixes (set[str] | None, optional): The . Defaults to None.
        identifiers (dict[str, str] | None, optional): _description_. Defaults to None.
        reduce_assignments (bool, optional): _description_. Defaults to False.
        expand_functions (set[str] | None, optional): _description_. Defaults to None.
        pre_transformers (Iterable[ast.NodeTransformer] | None, optional): _description_. Defaults to None.
        post_transformers (Iterable[ast.NodeTransformer] | None, optional): _description_. Defaults to None.
        plugins (Iterable[Plugin] | None, optional): _description_. Defaults to None.

    Returns:
        str: The LaTeX code.
    """
    tree = parse_function(fn)
    for transformer in (
        (pre_transformers or [])
        + default_transformers(
            prefixes=prefixes,
            identifiers=replace_identifiers,
            reduce_assignments=reduce_assignments,
            expand_functions=expand_functions,
        )
        + (post_transformers or [])
    ):
        tree = transformer.visit(tree)

    stack = default_stack(
        *(plugins or []),
        LatexifierClass(**kwargs),
        use_set_symbols=use_set_symbols,
        use_math_symbols=use_math_symbols,
        use_mathrm=use_mathrm,
        custom_identifiers=custom_identifiers,
    )
    latex = stack.visit(tree)

    if to_file and isinstance(latex, str):
        path = Path(to_file) if isinstance(to_file, str) else Path(f"{fn.__name__}.tex")
        if path.is_dir():
            path = path / f"{fn.__name__}.tex"
        path.write_text(latex)

    return latex
