"""NodeTransformer to trim unnecessary prefixes."""

from __future__ import annotations

import ast
import re

from latexify import ast_utils
from latexify.analyzers import analyze_attribute

_PREFIX_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$")


class PrefixTrimmer(ast.NodeTransformer):
    """NodeTransformer to trim unnecessary prefixes.

    This class investigates all Attribute subtrees, and replace them if the prefix of
    the attribute matches the given set of prefixes.
    Prefix is searched in the manner of leftmost longest matching.

    Args:
        prefixes: Set of prefixes to be trimmed. Nested prefix is allowed too.
            Each value must follow one of the following formats:
            - A Python identifier, e.g., "math"
            - Python identifiers joined by periods, e.g., "numpy.random"

    Example:
        def f(x):
            return math.sqrt(x)

        PrefixTrimmer({"math"}) will modify the AST of the function above to below:

        def f(x):
            return sqrt(x)
    """

    _prefixes: list[tuple[str, ...]]

    def __init__(self, prefixes: set[str]) -> None:
        for p in prefixes:
            if not _PREFIX_PATTERN.match(p):
                raise ValueError(f"Invalid prefix: {p}")

        self._prefixes = [tuple(p.split(".")) for p in prefixes]

    def visit_Attribute(self, node: ast.Attribute) -> ast.expr:
        """Visit an Attribute node."""
        prefix = analyze_attribute(node.value)

        # Performs leftmost longest match.
        # NOTE(odashi):
        # This implementation is very naive, but would work efficiently as long as the
        # number of patterns is small.
        matched_length = 0

        for p in self._prefixes:
            length = min(len(p), len(prefix))
            if prefix[:length] == p and length > matched_length:
                matched_length = length

        return ast_utils.make_attribute_nested(prefix[matched_length:] + (node.attr,))
