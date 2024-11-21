from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from latexify.ast_utils import parse_function
from latexify.codegen.function_codegen import FunctionCodegen
from latexify.codegen.plugin import Plugin
from latexify.codegen.plugin_stack import default_stack
from latexify.transformers.assignment_reducer import AssignmentReducer
from latexify.transformers.aug_assign_replacer import AugAssignReplacer
from latexify.transformers.docstring_remover import DocstringRemover
from latexify.transformers.function_expander import FunctionExpander
from latexify.transformers.identifier_replacer import IdentifierReplacer
from latexify.transformers.prefix_trimmer import PrefixTrimmer

if TYPE_CHECKING:
    import ast
    from collections.abc import Generator, Iterable


def get_transformers(
    prefixes: set[str] | None = None,
    identifiers: dict[str, str] | None = None,
    reduce_assignments: bool = False,
    expand_functions: set[str] | None = None,
    pre_transformers: Iterable[ast.NodeTransformer] | None = None,
    post_transformers: Iterable[ast.NodeTransformer] | None = None,
    **_,
) -> Generator[ast.NodeTransformer, None, None]:
    """
    Get a generator of transformers to apply to the AST.

    Args:
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
        pre_transformers: Transformers to apply before the main transformers.
        post_transformers: Transformers to apply after the main transformers.
    """
    yield from pre_transformers or ()
    yield AugAssignReplacer()
    if prefixes is not None:
        yield PrefixTrimmer(prefixes)
    if identifiers is not None:
        yield IdentifierReplacer(identifiers)
    if reduce_assignments:
        yield DocstringRemover()
        yield AssignmentReducer()
    if expand_functions is not None:
        yield FunctionExpander(expand_functions)
    yield from post_transformers or ()


def get_latex(
    fn: Callable[..., Any],
    /,
    LatexifierClass: type[Plugin] = FunctionCodegen,  # noqa: N803
    to_file: str | None = None,
    **kwargs: Any,
) -> str:
    """Construct the stack of plugins"""
    tree = parse_function(fn)
    for transformer in get_transformers(**kwargs):
        tree = transformer.visit(tree)

    stack = default_stack(
        *kwargs.get("plugins", ()),
        LatexifierClass(**kwargs),
        use_set_symbols=kwargs.get("use_set_symbols"),
        use_math_symbols=kwargs.get("use_math_symbols"),
        use_mathrm=kwargs.get("use_mathrm"),
    )
    latex = stack.visit(tree)

    if to_file and isinstance(latex, str):
        path = Path(to_file) if isinstance(to_file, str) else Path(f"{fn.__name__}.tex")
        if path.is_dir():
            path = path / f"{fn.__name__}.tex"
        path.write_text(latex)

    return latex
