"""Latexify root package."""

# ruff: noqa: PLC0414

try:
    from latexify import _version

    __version__ = _version.__version__
except ImportError:
    __version__ = ""

from latexify.frontend import (
    algorithmic as algorithmic,
)
from latexify.frontend import (
    expression as expression,
)
from latexify.frontend import (
    function as function,
)
from latexify.generate_latex import (
    get_latex as get_latex,
)
