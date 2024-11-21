from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable


class LatexifyWrapper:
    """Object with LaTeX representation."""

    _fn: Callable[..., Any]
    _str: str
    _latex: str

    def __init__(self, fn: Callable[..., Any], s: str, latex: str) -> None:
        self._fn = fn
        self._str = s
        self._latex = latex

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

    def __call__(self, *args, **kwargs) -> Any:
        return self._fn(*args, **kwargs)

    def __str__(self) -> str:
        return self._str

    def _repr_latex_(self) -> str:
        """IPython hook to display LaTeX visualization.

        See https://ipython.readthedocs.io/en/stable/config/integrating.html
        """
        return self._latex
