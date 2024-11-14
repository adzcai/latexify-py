from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from latexify.analyzers import analyze_range, reduce_stop_parameter
from latexify.ast_utils import extract_function_name_or_none, extract_int_or_none
from latexify.exceptions import LatexifyError

if TYPE_CHECKING:
    from collections.abc import Callable


def _get_sum_prod_range(visitor, node: ast.comprehension) -> tuple[str, str] | None:
    """Helper to process range(...) for sum and prod functions.

    Args:
        node: comprehension node to be analyzed.

    Returns:
        Tuple of following strings:
            - lower_rhs
            - upper
        which are used in _get_sum_prod_info, or None if the analysis failed.
    """
    if not (isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name) and node.iter.func.id == "range"):
        return None

    try:
        range_info = analyze_range(node.iter)
    except LatexifyError:
        return None

    if (
        # Only accepts ascending order with step size 1.
        range_info.step_int != 1
        or (
            range_info.start_int is not None
            and range_info.stop_int is not None
            and range_info.start_int >= range_info.stop_int
        )
    ):
        return None

    lower_rhs = visitor.visit(range_info.start) if range_info.start_int is None else str(range_info.start_int)

    if range_info.stop_int is None:
        upper = visitor.visit(reduce_stop_parameter(range_info.stop))
    else:
        upper = str(range_info.stop_int - 1)

    return lower_rhs, upper


def _get_sum_prod_info(visitor, node: ast.GeneratorExp) -> tuple[str, list[tuple[str, str]]]:
    r"""Process GeneratorExp for sum and prod functions.

    Args:
        node: GeneratorExp node to be analyzed.

    Returns:
        Tuple of following strings:
            - elt
            - scripts
        which are used to represent sum/prod operators as follows:
            \sum_{scripts[0][0]}^{scripts[0][1]}
                \sum_{scripts[1][0]}^{scripts[1][1]}
                ...
                {elt}

    Raises:
        LateixfyError: Unsupported AST is given.
    """
    elt = visitor.visit(node.elt)

    scripts: list[tuple[str, str]] = []

    for comp in node.generators:
        range_args = _get_sum_prod_range(visitor, comp)

        if range_args is not None and not comp.ifs:
            target = visitor.visit(comp.target)
            lower_rhs, upper = range_args
            lower = f"{target} = {lower_rhs}"
        else:
            lower = visitor.visit(comp)  # Use a usual comprehension form.
            upper = ""

        scripts.append((lower, upper))

    return elt, scripts


def _generate_sum_prod(visitor, node: ast.Call) -> str | None:
    """Generates sum/prod expression.

    Args:
        node: ast.Call node containing the sum/prod invocation.

    Returns:
        Generated LaTeX, or None if the node has unsupported syntax.
    """
    if not node.args or not isinstance(node.args[0], ast.GeneratorExp):
        return None

    name = extract_function_name_or_none(node)
    assert name in ("fsum", "sum", "prod"), name

    command = {
        "fsum": r"\sum",
        "sum": r"\sum",
        "prod": r"\prod",
    }[name]

    elt, scripts = _get_sum_prod_info(visitor, node.args[0])
    scripts_str = [rf"{command}_{{{lo}}}^{{{up}}}" for lo, up in scripts]
    return " ".join(scripts_str) + rf" \mathopen{{}}\left({{{elt}}}\mathclose{{}}\right)"


def _generate_matrix(visitor, node: ast.Call) -> str | None:
    """Generates matrix expression.

    Args:
        node: ast.Call node containing the ndarray invocation.

    Returns:
        Generated LaTeX, or None if the node has unsupported syntax.
    """

    def generate_matrix_from_array(data: list[list[str]]) -> str:
        """Helper to generate a bmatrix environment."""
        contents = r" \\ ".join(" & ".join(row) for row in data)
        return r"\begin{bmatrix} " + contents + r" \end{bmatrix}"

    arg = node.args[0]
    if not isinstance(arg, ast.List) or not arg.elts:
        # Not an array or no rows
        return None

    row0 = arg.elts[0]

    if not isinstance(row0, ast.List):
        # Maybe 1 x N array
        return generate_matrix_from_array([[visitor.visit(x) for x in arg.elts]])

    if not row0.elts:
        # No columns
        return None

    ncols = len(row0.elts)

    rows: list[list[str]] = []

    for row in arg.elts:
        if not isinstance(row, ast.List) or len(row.elts) != ncols:
            # Length mismatch
            return None

        rows.append([visitor.visit(x) for x in row.elts])

    return generate_matrix_from_array(rows)


def _generate_zeros(visitor, node: ast.Call) -> str | None:
    """Generates LaTeX for numpy.zeros.
    Args:
        node: ast.Call node containing the appropriate method invocation.
    Returns:
        Generated LaTeX, or None if the node has unsupported syntax.
    """
    name = extract_function_name_or_none(node)
    assert name == "zeros", name

    if len(node.args) != 1:
        return None

    # All args to np.zeros should be numeric.
    if isinstance(node.args[0], ast.Tuple):
        dims = [extract_int_or_none(x) for x in node.args[0].elts]
        if any(x is None for x in dims):
            return None
        if not dims:
            return "0"
        if len(dims) == 1:
            dims = [1, dims[0]]

        dims_latex = r" \times ".join(str(x) for x in dims)
    else:
        dim = extract_int_or_none(node.args[0])
        if not isinstance(dim, int):
            return None
        # 1 x N array of zeros
        dims_latex = rf"1 \times {dim}"

    return rf"\mathbf{{0}}^{{{dims_latex}}}"


def _generate_identity(visitor, node: ast.Call) -> str | None:
    """Generates LaTeX for numpy.identity.
    Args:
        node: ast.Call node containing the appropriate method invocation.
    Returns:
        Generated LaTeX, or None if the node has unsupported syntax.
    """
    name = extract_function_name_or_none(node)
    assert name == "identity", name

    if len(node.args) != 1:
        return None

    ndims = extract_int_or_none(node.args[0])
    if ndims is None:
        return None

    return rf"\mathbf{{I}}_{{{ndims}}}"


def _generate_transpose(visitor, node: ast.Call) -> str | None:
    """Generates LaTeX for numpy.transpose.
    Args:
        node: ast.Call node containing the appropriate method invocation.
    Returns:
        Generated LaTeX, or None if the node has unsupported syntax.
    Raises:
        LatexifyError: Unsupported argument type given.
    """
    name = extract_function_name_or_none(node)
    assert name == "transpose", name

    if len(node.args) != 1:
        return None

    func_arg = node.args[0]
    if isinstance(func_arg, ast.Name):
        return rf"\mathbf{{{func_arg.id}}}^\intercal"
    else:
        return None


def _generate_determinant(visitor, node: ast.Call) -> str | None:
    """Generates LaTeX for numpy.linalg.det.
    Args:
        node: ast.Call node containing the appropriate method invocation.
    Returns:
        Generated LaTeX, or None if the node has unsupported syntax.
    Raises:
        LatexifyError: Unsupported argument type given.
    """
    name = extract_function_name_or_none(node)
    assert name == "det", name

    if len(node.args) != 1:
        return None

    func_arg = node.args[0]
    if isinstance(func_arg, ast.Name):
        arg_id = rf"\mathbf{{{func_arg.id}}}"
        return rf"\det \mathopen{{}}\left( {arg_id} \mathclose{{}}\right)"
    elif isinstance(func_arg, ast.List):
        matrix = _generate_matrix(visitor, node)
        return rf"\det \mathopen{{}}\left( {matrix} \mathclose{{}}\right)"

    return None


def _generate_matrix_rank(visitor, node: ast.Call) -> str | None:
    """Generates LaTeX for numpy.linalg.matrix_rank.
    Args:
        node: ast.Call node containing the appropriate method invocation.
    Returns:
        Generated LaTeX, or None if the node has unsupported syntax.
    Raises:
        LatexifyError: Unsupported argument type given.
    """
    name = extract_function_name_or_none(node)
    assert name == "matrix_rank", name

    if len(node.args) != 1:
        return None

    func_arg = node.args[0]
    if isinstance(func_arg, ast.Name):
        arg_id = rf"\mathbf{{{func_arg.id}}}"
        return rf"\mathrm{{rank}} \mathopen{{}}\left( {arg_id} \mathclose{{}}\right)"
    elif isinstance(func_arg, ast.List):
        matrix = _generate_matrix(visitor, node)
        return rf"\mathrm{{rank}} \mathopen{{}}\left( {matrix} \mathclose{{}}\right)"

    return None


def _generate_matrix_power(visitor, node: ast.Call) -> str | None:
    """Generates LaTeX for numpy.linalg.matrix_power.
    Args:
        node: ast.Call node containing the appropriate method invocation.
    Returns:
        Generated LaTeX, or None if the node has unsupported syntax.
    Raises:
        LatexifyError: Unsupported argument type given.
    """
    name = extract_function_name_or_none(node)
    assert name == "matrix_power", name

    if len(node.args) != 2:
        return None

    func_arg = node.args[0]
    power_arg = node.args[1]
    if isinstance(power_arg, ast.Num):
        if isinstance(func_arg, ast.Name):
            return rf"\mathbf{{{func_arg.id}}}^{{{power_arg.n}}}"
        elif isinstance(func_arg, ast.List):
            matrix = _generate_matrix(visitor, node)
            if matrix is not None:
                return rf"{matrix}^{{{power_arg.n}}}"
    return None


def _generate_inv(visitor, node: ast.Call) -> str | None:
    """Generates LaTeX for numpy.linalg.inv.
    Args:
        node: ast.Call node containing the appropriate method invocation.
    Returns:
        Generated LaTeX, or None if the node has unsupported syntax.
    Raises:
        LatexifyError: Unsupported argument type given.
    """
    name = extract_function_name_or_none(node)
    assert name == "inv", name

    if len(node.args) != 1:
        return None

    func_arg = node.args[0]
    if isinstance(func_arg, ast.Name):
        return rf"\mathbf{{{func_arg.id}}}^{{-1}}"
    elif isinstance(func_arg, ast.List):
        return rf"{_generate_matrix(visitor, node)}^{{-1}}"
    return None


def _generate_pinv(visitor, node: ast.Call) -> str | None:
    """Generates LaTeX for numpy.linalg.pinv.
    Args:
        node: ast.Call node containing the appropriate method invocation.
    Returns:
        Generated LaTeX, or None if the node has unsupported syntax.
    Raises:
        LatexifyError: Unsupported argument type given.
    """
    name = extract_function_name_or_none(node)
    assert name == "pinv", name

    if len(node.args) != 1:
        return None

    func_arg = node.args[0]
    if isinstance(func_arg, ast.Name):
        return rf"\mathbf{{{func_arg.id}}}^{{+}}"
    elif isinstance(func_arg, ast.List):
        return rf"{_generate_matrix(visitor, node)}^{{+}}"
    return None


custom_functions: dict[str, Callable[[ast.Call], str]] = {
    "fsum": _generate_sum_prod,
    "sum": _generate_sum_prod,
    "prod": _generate_sum_prod,
    "array": _generate_matrix,
    "ndarray": _generate_matrix,
    "zeros": _generate_zeros,
    "identity": _generate_identity,
    "transpose": _generate_transpose,
    "det": _generate_determinant,
    "matrix_rank": _generate_matrix_rank,
    "matrix_power": _generate_matrix_power,
    "inv": _generate_inv,
    "pinv": _generate_pinv,
}
