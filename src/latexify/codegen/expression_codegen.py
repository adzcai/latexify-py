"""Codegen for single expressions."""

from __future__ import annotations

import ast
import re
from typing import Any, Callable

from latexify import exceptions
from latexify.ast_utils import extract_function_name_or_none
from latexify.codegen import expression_rules
from latexify.codegen.custom_functions import custom_functions
from latexify.codegen.identifier_converter import IdentifierConverter


class ExpressionCodegen(ast.NodeVisitor):
    """Codegen for single expressions."""

    _identifier_converter: IdentifierConverter

    _bin_op_rules: dict[type[ast.operator], expression_rules.BinOpRule]
    _compare_ops: dict[type[ast.cmpop], str]

    def __init__(
        self,
        *,
        use_math_symbols: bool = False,
        use_set_symbols: bool = False,
        custom_functions: dict[str, Callable[[ast.Node], str]] = custom_functions,
    ) -> None:
        """Initializer.

        Args:
            use_math_symbols: Whether to convert identifiers with a math symbol
                surface (e.g., "alpha") to the LaTeX symbol (e.g., "\\alpha").
            use_set_symbols: Whether to use set symbols or not.
        """
        self._identifier_converter = IdentifierConverter(use_math_symbols=use_math_symbols)
        self._bin_op_rules = expression_rules.SET_BIN_OP_RULES if use_set_symbols else expression_rules.BIN_OP_RULES
        self._compare_ops = expression_rules.SET_COMPARE_OPS if use_set_symbols else expression_rules.COMPARE_OPS
        self._custom_functions = custom_functions

    def generic_visit(self, node: ast.AST) -> str:
        raise exceptions.LatexifyNotSupportedError(f"Unsupported AST: {type(node).__name__}")

    def visit_Tuple(self, node: ast.Tuple) -> str:
        """Visit a Tuple node."""
        elts = [self.visit(elt) for elt in node.elts]
        return r"\mathopen{}\left( " + r", ".join(elts) + r" \mathclose{}\right)"

    def visit_List(self, node: ast.List) -> str:
        """Visit a List node."""
        elts = [self.visit(elt) for elt in node.elts]
        return r"\mathopen{}\left[ " + r", ".join(elts) + r" \mathclose{}\right]"

    def visit_Set(self, node: ast.Set) -> str:
        """Visit a Set node."""
        elts = [self.visit(elt) for elt in node.elts]
        return r"\mathopen{}\left\{ " + r", ".join(elts) + r" \mathclose{}\right\}"

    def visit_ListComp(self, node: ast.ListComp) -> str:
        """Visit a ListComp node."""
        generators = [self.visit(comp) for comp in node.generators]
        return (
            r"\mathopen{}\left[ " + self.visit(node.elt) + r" \mid " + ", ".join(generators) + r" \mathclose{}\right]"
        )

    def visit_SetComp(self, node: ast.SetComp) -> str:
        """Visit a SetComp node."""
        generators = [self.visit(comp) for comp in node.generators]
        return (
            r"\mathopen{}\left\{ " + self.visit(node.elt) + r" \mid " + ", ".join(generators) + r" \mathclose{}\right\}"
        )

    def visit_comprehension(self, node: ast.comprehension) -> str:
        """Visit a comprehension node."""
        target = rf"{self.visit(node.target)} \in {self.visit(node.iter)}"

        if not node.ifs:
            # Returns the source without parenthesis.
            return target

        conds = [target] + [self.visit(cond) for cond in node.ifs]
        wrapped = [r"\mathopen{}\left( " + s + r" \mathclose{}\right)" for s in conds]
        return r" \land ".join(wrapped)

    def visit_Call(self, node: ast.Call) -> str:
        """Visit a Call node."""
        func_name = extract_function_name_or_none(node)

        # Special treatments for some functions.
        if func_name in self._custom_functions and (out := self._custom_functions[func_name](self, node)) is not None:
            return out

        # Obtains the codegen rule.
        rule = expression_rules.BUILTIN_FUNCS.get(func_name) if func_name is not None else None

        if rule is None:
            rule = expression_rules.FunctionRule(self.visit(node.func))

        if rule.is_unary and len(node.args) == 1:
            # Unary function. Applies the same wrapping policy with the unary operators.
            precedence = expression_rules.get_precedence(node)
            arg = node.args[0]
            # NOTE(odashi):
            # Factorial "x!" is treated as a special case: it requires both inner/outer
            # parentheses for correct interpretation.
            force_wrap_factorial = isinstance(arg, ast.Call) and (
                func_name == "factorial" or extract_function_name_or_none(arg) == "factorial"
            )
            # Note(odashi):
            # Wrapping is also required if the argument is pow.
            # https://github.com/google/latexify_py/issues/189
            force_wrap_pow = isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Pow)
            arg_latex = self._wrap_operand(arg, precedence, force_wrap=force_wrap_factorial or force_wrap_pow)
            elements = [rule.left, arg_latex, rule.right]
        else:
            arg_latex = ", ".join(self.visit(arg) for arg in node.args)
            if rule.is_wrapped:
                elements = [rule.left, arg_latex, rule.right]
            else:
                elements = [
                    rule.left,
                    r"\mathopen{}\left(",
                    arg_latex,
                    r"\mathclose{}\right)",
                    rule.right,
                ]

        return " ".join(x for x in elements if x)

    def visit_Attribute(self, node: ast.Attribute) -> str:
        """Visit an Attribute node."""
        vstr = self.visit(node.value)
        astr = self._identifier_converter.convert(node.attr)[0]
        return vstr + "." + astr

    def visit_Name(self, node: ast.Name) -> str:
        """Visit a Name node."""
        return self._identifier_converter.convert(node.id)[0]

    # From Python 3.8
    def visit_Constant(self, node: ast.Constant) -> str:
        """Visit a Constant node."""
        return convert_constant(node.value)

    # Until Python 3.7
    def visit_Num(self, node: ast.Num) -> str:
        """Visit a Num node."""
        return convert_constant(node.n)

    # Until Python 3.7
    def visit_Str(self, node: ast.Str) -> str:
        """Visit a Str node."""
        return convert_constant(node.s)

    # Until Python 3.7
    def visit_Bytes(self, node: ast.Bytes) -> str:
        """Visit a Bytes node."""
        return convert_constant(node.s)

    # Until Python 3.7
    def visit_NameConstant(self, node: ast.NameConstant) -> str:
        """Visit a NameConstant node."""
        return convert_constant(node.value)

    # Until Python 3.7
    def visit_Ellipsis(self, _node: ast.Ellipsis) -> str:
        """Visit an Ellipsis node."""
        return convert_constant(...)

    def _wrap_operand(self, child: ast.expr, parent_prec: int, *, force_wrap: bool = False) -> str:
        """Wraps the operand subtree with parentheses.

        Args:
            child: Operand subtree.
            parent_prec: Precedence of the parent operator.
            force_wrap: Whether to wrap the operand or not when the precedence is equal.

        Returns:
            LaTeX form of `child`, with or without surrounding parentheses.
        """
        latex = self.visit(child)
        child_prec = expression_rules.get_precedence(child)

        if force_wrap or child_prec < parent_prec:
            return rf"\mathopen{{}}\left( {latex} \mathclose{{}}\right)"

        return latex

    def _wrap_binop_operand(
        self,
        child: ast.expr,
        parent_prec: int,
        operand_rule: expression_rules.BinOperandRule,
    ) -> str:
        """Wraps the operand subtree of BinOp with parentheses.

        Args:
            child: Operand subtree.
            parent_prec: Precedence of the parent operator.
            operand_rule: Syntax rule of this operand.

        Returns:
            LaTeX form of the `child`, with or without surrounding parentheses.
        """
        if not operand_rule.wrap:
            return self.visit(child)

        if isinstance(child, ast.Call):
            child_fn_name = extract_function_name_or_none(child)
            rule = expression_rules.BUILTIN_FUNCS.get(child_fn_name) if child_fn_name is not None else None
            if rule is not None and rule.is_wrapped:
                return self.visit(child)

        if not isinstance(child, ast.BinOp):
            return self._wrap_operand(child, parent_prec)

        latex = self.visit(child)

        if expression_rules.BIN_OP_RULES[type(child.op)].is_wrapped:
            return latex

        child_prec = expression_rules.get_precedence(child)

        if child_prec > parent_prec or (child_prec == parent_prec and not operand_rule.force):
            return latex

        return rf"\mathopen{{}}\left( {latex} \mathclose{{}}\right)"

    _l_bracket_pattern = re.compile(r"^\\mathopen.*")
    _r_bracket_pattern = re.compile(r".*\\mathclose[^ ]+$")
    _r_word_pattern = re.compile(r"\\mathrm\{[^ ]+\}$")

    def _should_remove_multiply_op(self, l_latex: str, r_latex: str, l_expr: ast.expr, r_expr: ast.expr):
        """Determine whether the multiply operator should be removed or not.

        See also:
        https://github.com/google/latexify_py/issues/89#issuecomment-1344967636

        This is an ad-hoc implementation.
        This function doesn't fully implements the above requirements, but only
        essential ones necessary to release v0.3.
        """

        # NOTE(odashi): For compatibility with Python 3.7, we compare the generated
        # caracter type directly to determine the "numeric" type.

        if isinstance(l_expr, ast.Call):
            l_type = "f"
        elif self._r_bracket_pattern.match(l_latex):
            l_type = "b"
        elif self._r_word_pattern.match(l_latex):
            l_type = "w"
        elif l_latex[-1].isnumeric():
            l_type = "n"
        else:
            le = l_expr
            while True:
                if isinstance(le, ast.UnaryOp):
                    le = le.operand
                elif isinstance(le, ast.BinOp):
                    le = le.right
                elif isinstance(le, ast.Compare):
                    le = le.comparators[-1]
                elif isinstance(le, ast.BoolOp):
                    le = le.values[-1]
                else:
                    break
            l_type = "a" if isinstance(le, ast.Name) and len(le.id) == 1 else "m"

        if isinstance(r_expr, ast.Call):
            r_type = "f"
        elif self._l_bracket_pattern.match(r_latex):
            r_type = "b"
        elif r_latex.startswith("\\mathrm"):
            r_type = "w"
        elif r_latex[0].isnumeric():
            r_type = "n"
        else:
            re = r_expr
            while True:
                if isinstance(re, ast.UnaryOp):
                    if isinstance(re.op, ast.USub):
                        # NOTE(odashi): Unary "-" always require \cdot.
                        return False
                    re = re.operand
                elif isinstance(re, (ast.BinOp, ast.Compare)):
                    re = re.left
                elif isinstance(re, ast.BoolOp):
                    re = re.values[0]
                else:
                    break
            r_type = "a" if isinstance(re, ast.Name) and len(re.id) == 1 else "m"

        if r_type == "n":
            return False
        if l_type in "bn":
            return True
        if l_type in "am" and r_type in "am":
            return True
        return False

    def visit_BinOp(self, node: ast.BinOp) -> str:
        """Visit a BinOp node."""
        prec = expression_rules.get_precedence(node)
        rule = self._bin_op_rules[type(node.op)]
        lhs = self._wrap_binop_operand(node.left, prec, rule.operand_left)
        rhs = self._wrap_binop_operand(node.right, prec, rule.operand_right)

        if type(node.op) in [ast.Mult, ast.MatMult] and self._should_remove_multiply_op(
            lhs, rhs, node.left, node.right
        ):
            return f"{rule.latex_left}{lhs} {rhs}{rule.latex_right}"

        return f"{rule.latex_left}{lhs}{rule.latex_middle}{rhs}{rule.latex_right}"

    def visit_UnaryOp(self, node: ast.UnaryOp) -> str:
        """Visit a UnaryOp node."""
        latex = self._wrap_operand(node.operand, expression_rules.get_precedence(node))
        return expression_rules.UNARY_OPS[type(node.op)] + latex

    def visit_Compare(self, node: ast.Compare) -> str:
        """Visit a Compare node."""
        parent_prec = expression_rules.get_precedence(node)
        lhs = self._wrap_operand(node.left, parent_prec)
        ops = [self._compare_ops[type(x)] for x in node.ops]
        rhs = [self._wrap_operand(x, parent_prec) for x in node.comparators]
        ops_rhs = [f" {o} {r}" for o, r in zip(ops, rhs)]
        return lhs + "".join(ops_rhs)

    def visit_BoolOp(self, node: ast.BoolOp) -> str:
        """Visit a BoolOp node."""
        parent_prec = expression_rules.get_precedence(node)
        values = [self._wrap_operand(x, parent_prec) for x in node.values]
        op = f" {expression_rules.BOOL_OPS[type(node.op)]} "
        return op.join(values)

    def visit_IfExp(self, node: ast.IfExp) -> str:
        """Visit an IfExp node"""
        latex = r"\left\{ \begin{array}{ll} "

        current_expr: ast.expr = node

        while isinstance(current_expr, ast.IfExp):
            cond_latex = self.visit(current_expr.test)
            true_latex = self.visit(current_expr.body)
            latex += true_latex + r", & \mathrm{if} \ " + cond_latex + r" \\ "
            current_expr = current_expr.orelse

        latex += self.visit(current_expr)
        return latex + r", & \mathrm{otherwise} \end{array} \right."

    # Until 3.8
    def visit_Index(self, node: ast.Index) -> str:
        """Visit an Index node."""
        return self.visit(node.value)  # type: ignore[attr-defined]

    def _convert_nested_subscripts(self, node: ast.Subscript) -> tuple[str, list[str]]:
        """Helper function to convert nested subscription.

        This function converts x[i][j][...] to "x" and ["i", "j", ...]

        Args:
            node: ast.Subscript node to be converted.

        Returns:
            Tuple of following strings:
                - The root value of the subscription.
                - Sequence of incices.
        """
        if isinstance(node.value, ast.Subscript):
            value, indices = self._convert_nested_subscripts(node.value)
        else:
            value = self.visit(node.value)
            indices = []

        indices.append(self.visit(node.slice))
        return value, indices

    def visit_Subscript(self, node: ast.Subscript) -> str:
        """Visitor a Subscript node."""
        value, indices = self._convert_nested_subscripts(node)

        # TODO(odashi): "[i][j][...]" may be a possible representation as well as "i, j. ..."
        indices_str = ", ".join(indices)

        return f"{value}_{{{indices_str}}}"


def convert_constant(value: Any) -> str:
    """Helper to convert constant values to LaTeX.

    Args:
        value: A constant value.

    Returns:
        The LaTeX representation of `value`.
    """
    if value is None or isinstance(value, bool):
        return r"\mathrm{" + str(value) + "}"
    if isinstance(value, (int, float, complex)):
        # TODO(odashi): Support other symbols for the imaginary unit than j.
        return str(value)
    if isinstance(value, str):
        return r'\textrm{"' + value + '"}'
    if isinstance(value, bytes):
        return r"\textrm{" + str(value) + "}"
    if value is ...:
        return r"\cdots"
    raise exceptions.LatexifyNotSupportedError(f"Unrecognized constant: {type(value).__name__}")
