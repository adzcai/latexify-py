"""Codegen rules for single expressions."""

from __future__ import annotations

import ast
import functools
from dataclasses import dataclass, field

# Precedences of operators for BoolOp, BinOp, UnaryOp, and Compare nodes.
# Note that this value affects only the appearance of surrounding parentheses for each
# expression, and does not affect the AST itself.
# See also:
# https://docs.python.org/3/reference/expressions.html#operator-precedence
_PRECEDENCES: dict[type[ast.AST], int] = {
    ast.Pow: 120,
    ast.UAdd: 110,
    ast.USub: 110,
    ast.Invert: 110,
    ast.Mult: 100,
    ast.MatMult: 100,
    ast.Div: 100,
    ast.FloorDiv: 100,
    ast.Mod: 100,
    ast.Add: 90,
    ast.Sub: 90,
    ast.LShift: 80,
    ast.RShift: 80,
    ast.BitAnd: 70,
    ast.BitXor: 60,
    ast.BitOr: 50,
    ast.In: 40,
    ast.NotIn: 40,
    ast.Is: 40,
    ast.IsNot: 40,
    ast.Lt: 40,
    ast.LtE: 40,
    ast.Gt: 40,
    ast.GtE: 40,
    ast.NotEq: 40,
    ast.Eq: 40,
    # NOTE(odashi):
    # We assume that the `not` operator has the same precedence with other unary
    # operators `+`, `-` and `~`, because the LaTeX counterpart $\lnot$ looks to have a
    # high precedence.
    # ast.Not: 30,
    ast.Not: 110,
    ast.And: 20,
    ast.Or: 10,
}

# NOTE(odashi):
# Function invocation is treated as a unary operator with a higher precedence.
# This ensures that the argument with a unary operator is wrapped:
#     exp(x) --> \exp x
#     exp(-x) --> \exp (-x)
#     -exp(x) --> - \exp x
_CALL_PRECEDENCE = _PRECEDENCES[ast.UAdd] + 1

_INF_PRECEDENCE = 1_000_000


def get_precedence(node: ast.AST) -> int:
    """Obtains the precedence of the subtree.

    Args:
        node: Subtree to investigate.

    Returns:
        If `node` is a subtree with some operator, returns the precedence of the
        operator. Otherwise, returns a number larger enough from other precedences.
    """
    if isinstance(node, ast.Call):
        return _CALL_PRECEDENCE

    if isinstance(node, (ast.BinOp, ast.UnaryOp, ast.BoolOp)):
        return _PRECEDENCES[type(node.op)]

    if isinstance(node, ast.Compare):
        # Compare operators have the same precedence. It is enough to check only the
        # first operator.
        return _PRECEDENCES[type(node.ops[0])]

    return _INF_PRECEDENCE


@dataclass(frozen=True)
class BinOperandRule:
    """
    A class to define rules for binary operands.

    Attributes:
        wrap (bool): Whether to require wrapping operands by parentheses according to the precedence.
        force (bool): Whether to require wrapping operands by parentheses if the operand has the same
            precedence with this operator. This is used to control the behavior of non-associative operators.
    """

    wrap: bool = True
    force: bool = False


@dataclass(frozen=True)
class BinOpRule:
    """Syntax rules for BinOp."""

    # Left/middle/right syntaxes to wrap operands.
    latex_left: str
    latex_middle: str
    latex_right: str

    # Operand rules.
    operand_left: BinOperandRule = field(default_factory=BinOperandRule)
    operand_right: BinOperandRule = field(default_factory=BinOperandRule)

    # Whether to assume the resulting syntax is wrapped by some bracket operators.
    # If True, the parent operator can avoid wrapping this operator by parentheses.
    is_wrapped: bool = False


BIN_OP_RULES: dict[type[ast.operator], BinOpRule] = {
    ast.Pow: BinOpRule(
        "",
        "^{",
        "}",
        operand_left=BinOperandRule(force=True),
        operand_right=BinOperandRule(wrap=False),
    ),
    ast.Mult: BinOpRule("", r" \cdot ", ""),
    ast.MatMult: BinOpRule("", r" \cdot ", ""),
    ast.Div: BinOpRule(
        r"\frac{",
        "}{",
        "}",
        operand_left=BinOperandRule(wrap=False),
        operand_right=BinOperandRule(wrap=False),
    ),
    ast.FloorDiv: BinOpRule(
        r"\left\lfloor\frac{",
        "}{",
        r"}\right\rfloor",
        operand_left=BinOperandRule(wrap=False),
        operand_right=BinOperandRule(wrap=False),
        is_wrapped=True,
    ),
    ast.Mod: BinOpRule("", r" \mathbin{\%} ", "", operand_right=BinOperandRule(force=True)),
    ast.Add: BinOpRule("", " + ", ""),
    ast.Sub: BinOpRule("", " - ", "", operand_right=BinOperandRule(force=True)),
    ast.LShift: BinOpRule("", r" \ll ", "", operand_right=BinOperandRule(force=True)),
    ast.RShift: BinOpRule("", r" \gg ", "", operand_right=BinOperandRule(force=True)),
    ast.BitAnd: BinOpRule("", r" \mathbin{\&} ", ""),
    ast.BitXor: BinOpRule("", r" \oplus ", ""),
    ast.BitOr: BinOpRule("", r" \mathbin{|} ", ""),
}

# Typeset for BinOp of sets.
SET_BIN_OP_RULES: dict[type[ast.operator], BinOpRule] = {
    **BIN_OP_RULES,
    ast.Sub: BinOpRule("", r" \setminus ", "", operand_right=BinOperandRule(force=True)),
    ast.BitAnd: BinOpRule("", r" \cap ", ""),
    ast.BitXor: BinOpRule("", r" \mathbin{\triangle} ", ""),
    ast.BitOr: BinOpRule("", r" \cup ", ""),
}

UNARY_OPS: dict[type[ast.unaryop], str] = {
    ast.Invert: r"\mathord{\sim} ",
    ast.UAdd: "+",  # Explicitly adds the $+$ operator.
    ast.USub: "-",
    ast.Not: r"\lnot ",
}

COMPARE_OPS: dict[type[ast.cmpop], str] = {
    ast.Eq: "=",
    ast.Gt: ">",
    ast.GtE: r"\ge",
    ast.In: r"\in",
    ast.Is: r"\equiv",
    ast.IsNot: r"\not\equiv",
    ast.Lt: "<",
    ast.LtE: r"\le",
    ast.NotEq: r"\ne",
    ast.NotIn: r"\notin",
}

# Typeset for Compare of sets.
SET_COMPARE_OPS: dict[type[ast.cmpop], str] = {
    **COMPARE_OPS,
    ast.Gt: r"\supset",
    ast.GtE: r"\supseteq",
    ast.Lt: r"\subset",
    ast.LtE: r"\subseteq",
}

BOOL_OPS: dict[type[ast.boolop], str] = {
    ast.And: r"\land",
    ast.Or: r"\lor",
}


@dataclass(frozen=True)
class FunctionRule:
    """Codegen rules for functions.

    Attributes:
        left: LaTeX expression concatenated to the left-hand side of the arguments.
        right: LaTeX expression concatenated to the right-hand side of the arguments.
        is_unary: Whether the function is treated as a unary operator or not.
        is_wrapped: Whether the resulting syntax is wrapped by brackets or not.
    """

    left: str
    right: str = ""
    is_unary: bool = False
    is_wrapped: bool = False


_UnaryRule = functools.partial(FunctionRule, is_unary=True)

_WrappedRule = functools.partial(FunctionRule, is_wrapped=True)


# from the builtin math package
# name => left_syntax, right_syntax, is_wrapped
BUILTIN_FUNCS: dict[str, FunctionRule] = {
    "abs": _WrappedRule(r"\mathopen{}\left|", r"\mathclose{}\right|"),
    "acos": _UnaryRule(r"\arccos"),
    "acosh": _UnaryRule(r"\mathrm{arcosh}"),
    "arccos": _UnaryRule(r"\arccos"),
    "arccot": _UnaryRule(r"\mathrm{arccot}"),
    "arccsc": _UnaryRule(r"\mathrm{arccsc}"),
    "arcosh": _UnaryRule(r"\mathrm{arcosh}"),
    "arcoth": _UnaryRule(r"\mathrm{arcoth}"),
    "arcsec": _UnaryRule(r"\mathrm{arcsec}"),
    "arcsch": _UnaryRule(r"\mathrm{arcsch}"),
    "arcsin": _UnaryRule(r"\arcsin"),
    "arctan": _UnaryRule(r"\arctan"),
    "arsech": _UnaryRule(r"\mathrm{arsech}"),
    "arsinh": _UnaryRule(r"\mathrm{arsinh}"),
    "artanh": _UnaryRule(r"\mathrm{artanh}"),
    "asin": _UnaryRule(r"\arcsin"),
    "asinh": _UnaryRule(r"\mathrm{arsinh}"),
    "atan": _UnaryRule(r"\arctan"),
    "atanh": _UnaryRule(r"\mathrm{artanh}"),
    "ceil": _WrappedRule(r"\mathopen{}\left\lceil", r"\mathclose{}\right\rceil"),
    "cos": _UnaryRule(r"\cos"),
    "cosh": _UnaryRule(r"\cosh"),
    "cot": _UnaryRule(r"\cot"),
    "coth": _UnaryRule(r"\coth"),
    "csc": _UnaryRule(r"\csc"),
    "csch": _UnaryRule(r"\mathrm{csch}"),
    "exp": _UnaryRule(r"\exp"),
    "fabs": _WrappedRule(r"\mathopen{}\left|", r"\mathclose{}\right|"),
    "factorial": _UnaryRule("", right="!"),
    "floor": _WrappedRule(r"\mathopen{}\left\lfloor", r"\mathclose{}\right\rfloor"),
    "fsum": _UnaryRule(r"\sum"),
    "gamma": _UnaryRule(r"\Gamma"),
    "log": _UnaryRule(r"\log"),
    "log10": _UnaryRule(r"\log_{10}"),
    "log2": _UnaryRule(r"\log_2"),
    "prod": _UnaryRule(r"\prod"),
    "sec": _UnaryRule(r"\sec"),
    "sech": _UnaryRule(r"\mathrm{sech}"),
    "sin": _UnaryRule(r"\sin"),
    "sinh": _UnaryRule(r"\sinh"),
    "sqrt": _WrappedRule(r"\sqrt{", "}"),
    "sum": _UnaryRule(r"\sum"),
    "tan": _UnaryRule(r"\tan"),
    "tanh": _UnaryRule(r"\tanh"),
}
