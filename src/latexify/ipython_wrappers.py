"""Wrapper objects for IPython to display output."""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Any, Callable, cast

from latexify import generate_latex
from latexify.exceptions import LatexifyError


class LatexifiedRepr(metaclass=ABCMeta):
    """Object with LaTeX representation."""

    _fn: Callable[..., Any]

    def __init__(self, fn: Callable[..., Any], **kwargs) -> None:
        self._fn = fn

    @property
    def __doc__(self) -> str | None:
        return self._fn.__doc__

    @__doc__.setter
    def __doc__(self, val: str | None) -> None:
        self._fn.__doc__ = val

    @property
    def __name__(self) -> str:
        return self._fn.__name__

    @__name__.setter
    def __name__(self, val: str) -> None:
        self._fn.__name__ = val

    # After Python 3.7
    # @final
    def __call__(self, *args, **kwargs) -> Any:
        return self._fn(*args, **kwargs)

    @abstractmethod
    def __str__(self) -> str: ...

    @abstractmethod
    def _repr_html_(self) -> str | tuple[str, dict[str, Any]] | None:
        """IPython hook to display HTML visualization.
        
        See https://ipython.readthedocs.io/en/stable/config/integrating.html
        """

    @abstractmethod
    def _repr_latex_(self) -> str | tuple[str, dict[str, Any]] | None:
        """IPython hook to display LaTeX visualization.
        
        See https://ipython.readthedocs.io/en/stable/config/integrating.html
        """


class LatexifiedAlgorithm(LatexifiedRepr):
    """Algorithm with latex representation.
    
    IPython does not come with the `algpseudocode` LaTeX package,
    so we provide an alternative _ipython_latex representation.
    """

    _latex: str | LatexifyError
    _ipython_latex: str | LatexifyError

    def __init__(self, fn: Callable[..., Any], **kwargs) -> None:
        super().__init__(fn)

        try:
            self._latex = generate_latex.get_latex(
                fn, style=generate_latex.Style.ALGORITHMIC, **kwargs
            )
        except LatexifyError as e:
            self._latex = e

        try:
            self._ipython_latex = generate_latex.get_latex(
                fn, style=generate_latex.Style.IPYTHON_ALGORITHMIC, **kwargs
            )
        except LatexifyError as e:
            self._ipython_latex = e

    def __str__(self) -> str:
        return (
            self._latex
            if isinstance(self._latex, str)
            else self._latex.describe()
        )

    def _repr_html_(self) -> str | tuple[str, dict[str, Any]] | None:
        """IPython hook to display HTML visualization."""
        return (
            '<span style="color: red;">'
            + (
                "HTML output not supported"
                if isinstance(self._ipython_latex, str)
                else self._ipython_latex.describe()
            )
            + "</span>"
        )

    def _repr_latex_(self) -> str | tuple[str, dict[str, Any]] | None:
        """IPython hook to display LaTeX visualization."""
        return (
            f"$ {self._ipython_latex} $"
            if isinstance(self._ipython_latex, str)
            else self._ipython_latex.describe()
        )


class LatexifiedFunction(LatexifiedRepr):
    """Function with latex representation."""

    _latex: str | LatexifyError

    def __init__(self, fn: Callable[..., Any], **kwargs) -> None:
        super().__init__(fn, **kwargs)

        try:
            self._latex = self._latex = generate_latex.get_latex(
                fn, style=generate_latex.Style.FUNCTION, **kwargs
            )
            self._error = None
        except LatexifyError as e:
            self._latex = None
            self._error = f"{type(e).__name__}: {e!s}"

    def __str__(self) -> str:
        return self._latex if self._latex is not None else cast(str, self._error)

    def _repr_html_(self) -> str | tuple[str, dict[str, Any]] | None:
        """IPython hook to display HTML visualization."""
        return (
            '<span style="color: red;">' + self._error + "</span>"
            if self._error is not None
            else None
        )

    def _repr_latex_(self) -> str | tuple[str, dict[str, Any]] | None:
        """IPython hook to display LaTeX visualization."""
        return (
            rf"$$ \displaystyle {self._latex} $$"
            if self._latex is not None
            else self._error
        )
