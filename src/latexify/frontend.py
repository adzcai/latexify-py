"""Frontend interfaces of latexify."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any, overload

from latexify.codegen.algorithmic_codegen import AlgorithmicCodegen, IPythonLatexifier
from latexify.codegen.function_codegen import FunctionCodegen
from latexify.exceptions import LatexifyError
from latexify.generate_latex import get_latex
from latexify.ipython_wrappers import LatexifyWrapper

if TYPE_CHECKING:
    import ast
    from collections.abc import Callable, Iterable



@overload
def algorithmic(fn: Callable[..., Any], to_file: str | None = None, **kwargs: Any) -> LatexifyWrapper: ...


@overload
def algorithmic(
    **kwargs: Any,
) -> Callable[[Callable[..., Any]], LatexifyWrapper]: ...


def algorithmic(
    fn: Callable[..., Any] | None = None, **kwargs: Any
) -> LatexifyWrapper | Callable[[Callable[..., Any]], LatexifyWrapper]:
    """Attach LaTeX pretty-printing to the given function.

    This function works with or without specifying the target function as the
    positional argument. The following two syntaxes works similarly.
        - latexify.algorithmic(alg, **kwargs)
        - latexify.algorithmic(**kwargs)(alg)

    Args:
        fn: Callable to be wrapped.
        **kwargs: Arguments to control behavior. See also get_latex().

    Returns:
        - If `fn` is passed, returns the wrapped function.
        - Otherwise, returns the wrapper function with given settings.
    """
    if fn is not None:
        try:
            algpseudocode = get_latex(fn, LatexifierClass=AlgorithmicCodegen, **kwargs)
        except LatexifyError as e:
            algpseudocode = _describe_error(e)

        try:
            latex = get_latex(fn, LatexifierClass=IPythonLatexifier, **kwargs)
        except LatexifyError as e:
            latex = _describe_error(e)
        else:
            latex = f"$ {latex} $"

        return LatexifyWrapper(fn, algpseudocode, latex)

    return partial(algorithmic, **kwargs)


@overload
def function(fn: Callable[..., Any], **kwargs: Any) -> LatexifyWrapper: ...


@overload
def function(
    **kwargs: Any,
) -> Callable[[Callable[..., Any]], LatexifyWrapper]: ...


def function(
    fn: Callable[..., Any] | None = None, **kwargs: Any
) -> LatexifyWrapper | Callable[[Callable[..., Any]], LatexifyWrapper]:
    """Attach LaTeX pretty-printing to the given function.

    This function works with or without specifying the target function as the positional
    argument. The following two syntaxes works similarly.
        - latexify.function(fn, **kwargs)
        - latexify.function(**kwargs)(fn)

    Args:
        fn: Callable to be wrapped.
        **kwargs: Arguments to control behavior. See also get_latex().

    Returns:
        - If `fn` is passed, returns the wrapped function.
        - Otherwise, returns the wrapper function with given settings.
    """
    if fn is not None:
        try:
            latex = get_latex(fn, LatexifierClass=FunctionCodegen, **kwargs)
        except LatexifyError as e:
            s = latex = _describe_error(e)
        else:
            s, latex = latex, f"$$ \\displaystyle {latex} $$"
        return LatexifyWrapper(fn, s, latex)

    return partial(function, **kwargs)


@overload
def expression(fn: Callable[..., Any], **kwargs: Any) -> LatexifyWrapper: ...


@overload
def expression(
    prefixes: set[str] | None = None,
    identifiers: dict[str, str] | None = None,
    reduce_assignments: bool = False,
    expand_functions: set[str] | None = None,
    pre_transformers: Iterable[ast.NodeTransformer] | None = None,
    post_transformers: Iterable[ast.NodeTransformer] | None = None,
    use_math_symbols: bool = True,
    use_set_symbols: bool = False,
    use_signature: bool = True,
) -> Callable[[Callable[..., Any]], LatexifyWrapper]: ...


def expression(
    fn: Callable[..., Any] | None = None, **kwargs: Any
) -> LatexifyWrapper | Callable[[Callable[..., Any]], LatexifyWrapper]:
    """Attach LaTeX pretty-printing to the given function.

    This function is a shortcut for `latexify.function` with the default parameter
    `use_signature=False`.
    """
    kwargs.setdefault("use_signature", False)
    return function(fn, **kwargs)


def _describe_error(e):
    return f"{e.__class__.__name__}: {e!s}"
