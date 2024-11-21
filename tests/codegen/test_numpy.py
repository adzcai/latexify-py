import ast

import pytest

from tests.utils import assert_expr_equal


@pytest.mark.parametrize(
    ("code", "latex"),
    [
        ("array([1])", r"\begin{bmatrix} 1 \end{bmatrix}"),
        ("array([1, 2, 3])", r"\begin{bmatrix} 1 & 2 & 3 \end{bmatrix}"),
        ("array([[1]])", r"\begin{bmatrix} 1 \end{bmatrix}"),
        ("array([[1], [2], [3]])", r"\begin{bmatrix} 1 \\ 2 \\ 3 \end{bmatrix}"),
        (
            "array([[1, 2], [3, 4], [5, 6]])",
            r"\begin{bmatrix} 1 & 2 \\ 3 & 4 \\ 5 & 6 \end{bmatrix}",
        ),
        ("ndarray([1])", r"\begin{bmatrix} 1 \end{bmatrix}"),
    ],
)
def test_numpy_array(code: str, latex: str) -> None:
    assert_expr_equal(code, ast.Call, latex)


@pytest.mark.parametrize(
    ("code", "latex"),
    [
        ("array(1)", r"\mathrm{array} \mathopen{}\left( 1 \mathclose{}\right)"),
        (
            "array([])",
            r"\mathrm{array} \mathopen{}\left(" r" \mathopen{}\left[  \mathclose{}\right]" r" \mathclose{}\right)",
        ),
        (
            "array([[]])",
            r"\mathrm{array} \mathopen{}\left("
            r" \mathopen{}\left[ \mathopen{}\left["
            r"  \mathclose{}\right] \mathclose{}\right]"
            r" \mathclose{}\right)",
        ),
        (
            "array([[1], [2], [3, 4]])",
            r"\mathrm{array} \mathopen{}\left("
            r" \mathopen{}\left["
            r" \mathopen{}\left[ 1 \mathclose{}\right],"
            r" \mathopen{}\left[ 2 \mathclose{}\right],"
            r" \mathopen{}\left[ 3, 4 \mathclose{}\right]"
            r" \mathclose{}\right]"
            r" \mathclose{}\right)",
        ),
        ("ndarray(1)", r"\mathrm{ndarray} \mathopen{}\left( 1 \mathclose{}\right)"),
    ],
)
def test_numpy_array_unsupported(code: str, latex: str) -> None:
    assert_expr_equal(code, ast.Call, latex)


@pytest.mark.parametrize(
    ("code", "latex"),
    [
        ("zeros(0)", r"\mathbf{0}^{1 \times 0}"),
        ("zeros(1)", r"\mathbf{0}^{1 \times 1}"),
        ("zeros(2)", r"\mathbf{0}^{1 \times 2}"),
        ("zeros(())", r"0"),
        ("zeros((0,))", r"\mathbf{0}^{1 \times 0}"),
        ("zeros((1,))", r"\mathbf{0}^{1 \times 1}"),
        ("zeros((2,))", r"\mathbf{0}^{1 \times 2}"),
        ("zeros((0, 0))", r"\mathbf{0}^{0 \times 0}"),
        ("zeros((1, 1))", r"\mathbf{0}^{1 \times 1}"),
        ("zeros((2, 3))", r"\mathbf{0}^{2 \times 3}"),
        ("zeros((0, 0, 0))", r"\mathbf{0}^{0 \times 0 \times 0}"),
        ("zeros((1, 1, 1))", r"\mathbf{0}^{1 \times 1 \times 1}"),
        ("zeros((2, 3, 5))", r"\mathbf{0}^{2 \times 3 \times 5}"),
        # Unsupported
        ("zeros()", r"\mathrm{zeros} \mathopen{}\left( \mathclose{}\right)"),
        ("zeros(x)", r"\mathrm{zeros} \mathopen{}\left( x \mathclose{}\right)"),
        ("zeros(0, x)", r"\mathrm{zeros} \mathopen{}\left( 0, x \mathclose{}\right)"),
        (
            "zeros((x,))",
            r"\mathrm{zeros} \mathopen{}\left(" r" \mathopen{}\left( x \mathclose{}\right)" r" \mathclose{}\right)",
        ),
    ],
)
def test_zeros(code: str, latex: str) -> None:
    assert_expr_equal(code, ast.Call, latex)


@pytest.mark.parametrize(
    ("code", "latex"),
    [
        ("identity(0)", r"\mathbf{I}_{0}"),
        ("identity(1)", r"\mathbf{I}_{1}"),
        ("identity(2)", r"\mathbf{I}_{2}"),
    ],
)
def test_identity(code: str, latex: str) -> None:
    assert_expr_equal(code, ast.Call, latex)


@pytest.mark.parametrize(
    ("code", "latex"),
    [
        ("identity()", r"\mathrm{identity} \mathopen{}\left( \mathclose{}\right)"),
        ("identity(x)", r"\mathrm{identity} \mathopen{}\left( x \mathclose{}\right)"),
        (
            "identity(0, x)",
            r"\mathrm{identity} \mathopen{}\left( 0, x \mathclose{}\right)",
        ),
    ],
)
def test_identity_unsupported(code: str, latex: str) -> None:
    assert_expr_equal(code, ast.Call, latex)


@pytest.mark.parametrize(
    ("code", "latex"),
    [
        ("transpose(A)", r"\mathbf{A}^\intercal"),
        ("transpose(b)", r"\mathbf{b}^\intercal"),
    ],
)
def test_transpose(code: str, latex: str) -> None:
    assert_expr_equal(code, ast.Call, latex)


@pytest.mark.parametrize(
    ("code", "latex"),
    [
        ("transpose()", r"\mathrm{transpose} \mathopen{}\left( \mathclose{}\right)"),
        ("transpose(2)", r"\mathrm{transpose} \mathopen{}\left( 2 \mathclose{}\right)"),
        (
            "transpose(a, (1, 0))",
            r"\mathrm{transpose} \mathopen{}\left( a, "
            r"\mathopen{}\left( 1, 0 \mathclose{}\right) \mathclose{}\right)",
        ),
    ],
)
def test_transpose_unsupported(code: str, latex: str) -> None:
    assert_expr_equal(code, ast.Call, latex)


@pytest.mark.parametrize(
    ("code", "latex"),
    [
        ("det(A)", r"\det \mathopen{}\left( \mathbf{A} \mathclose{}\right)"),
        ("det(b)", r"\det \mathopen{}\left( \mathbf{b} \mathclose{}\right)"),
        (
            "det([[1, 2], [3, 4]])",
            r"\det \mathopen{}\left( \begin{bmatrix} 1 & 2 \\" r" 3 & 4 \end{bmatrix} \mathclose{}\right)",
        ),
        (
            "det([[1, 2, 3], [4, 5, 6], [7, 8, 9]])",
            r"\det \mathopen{}\left( \begin{bmatrix} 1 & 2 & 3 \\ 4 & 5 & 6 \\"
            r" 7 & 8 & 9 \end{bmatrix} \mathclose{}\right)",
        ),
        # Unsupported
        ("det()", r"\mathrm{det} \mathopen{}\left( \mathclose{}\right)"),
        ("det(2)", r"\mathrm{det} \mathopen{}\left( 2 \mathclose{}\right)"),
        (
            "det(a, (1, 0))",
            r"\mathrm{det} \mathopen{}\left( a, " r"\mathopen{}\left( 1, 0 \mathclose{}\right) \mathclose{}\right)",
        ),
    ],
)
def test_determinant(code: str, latex: str) -> None:
    assert_expr_equal(code, ast.Call, latex)


@pytest.mark.parametrize(
    ("code", "latex"),
    [
        (
            "matrix_rank(A)",
            r"\mathrm{rank} \mathopen{}\left( \mathbf{A} \mathclose{}\right)",
        ),
        (
            "matrix_rank(b)",
            r"\mathrm{rank} \mathopen{}\left( \mathbf{b} \mathclose{}\right)",
        ),
        (
            "matrix_rank([[1, 2], [3, 4]])",
            r"\mathrm{rank} \mathopen{}\left( \begin{bmatrix} 1 & 2 \\" r" 3 & 4 \end{bmatrix} \mathclose{}\right)",
        ),
        (
            "matrix_rank([[1, 2, 3], [4, 5, 6], [7, 8, 9]])",
            r"\mathrm{rank} \mathopen{}\left( \begin{bmatrix} 1 & 2 & 3 \\ 4 & 5 & 6 \\"
            r" 7 & 8 & 9 \end{bmatrix} \mathclose{}\right)",
        ),
        # Unsupported
        (
            "matrix_rank()",
            r"\mathrm{matrix\_rank} \mathopen{}\left( \mathclose{}\right)",
        ),
        (
            "matrix_rank(2)",
            r"\mathrm{matrix\_rank} \mathopen{}\left( 2 \mathclose{}\right)",
        ),
        (
            "matrix_rank(a, (1, 0))",
            r"\mathrm{matrix\_rank} \mathopen{}\left( a, "
            r"\mathopen{}\left( 1, 0 \mathclose{}\right) \mathclose{}\right)",
        ),
    ],
)
def test_matrix_rank(code: str, latex: str) -> None:
    assert_expr_equal(code, ast.Call, latex)


@pytest.mark.parametrize(
    ("code", "latex"),
    [
        ("matrix_power(A, 2)", r"\mathbf{A}^{2}"),
        ("matrix_power(b, 2)", r"\mathbf{b}^{2}"),
        (
            "matrix_power([[1, 2], [3, 4]], 2)",
            r"\begin{bmatrix} 1 & 2 \\ 3 & 4 \end{bmatrix}^{2}",
        ),
        (
            "matrix_power([[1, 2, 3], [4, 5, 6], [7, 8, 9]], 42)",
            r"\begin{bmatrix} 1 & 2 & 3 \\ 4 & 5 & 6 \\ 7 & 8 & 9 \end{bmatrix}^{42}",
        ),
    ],
)
def test_matrix_power(code: str, latex: str) -> None:
    assert_expr_equal(code, ast.Call, latex)


@pytest.mark.parametrize(
    ("code", "latex"),
    [
        (
            "matrix_power()",
            r"\mathrm{matrix\_power} \mathopen{}\left( \mathclose{}\right)",
        ),
        (
            "matrix_power(2)",
            r"\mathrm{matrix\_power} \mathopen{}\left( 2 \mathclose{}\right)",
        ),
        (
            "matrix_power(a, (1, 0))",
            r"\mathrm{matrix\_power} \mathopen{}\left( a, "
            r"\mathopen{}\left( 1, 0 \mathclose{}\right) \mathclose{}\right)",
        ),
    ],
)
def test_matrix_power_unsupported(code: str, latex: str) -> None:
    assert_expr_equal(code, ast.Call, latex)


@pytest.mark.parametrize(
    ("code", "latex"),
    [
        ("inv(A)", r"\mathbf{A}^{-1}"),
        ("inv(b)", r"\mathbf{b}^{-1}"),
        ("inv([[1, 2], [3, 4]])", r"\begin{bmatrix} 1 & 2 \\ 3 & 4 \end{bmatrix}^{-1}"),
        (
            "inv([[1, 2, 3], [4, 5, 6], [7, 8, 9]])",
            r"\begin{bmatrix} 1 & 2 & 3 \\ 4 & 5 & 6 \\ 7 & 8 & 9 \end{bmatrix}^{-1}",
        ),
        # Unsupported
        ("inv()", r"\mathrm{inv} \mathopen{}\left( \mathclose{}\right)"),
        ("inv(2)", r"\mathrm{inv} \mathopen{}\left( 2 \mathclose{}\right)"),
        (
            "inv(a, (1, 0))",
            r"\mathrm{inv} \mathopen{}\left( a, " r"\mathopen{}\left( 1, 0 \mathclose{}\right) \mathclose{}\right)",
        ),
    ],
)
def test_inv(code: str, latex: str) -> None:
    assert_expr_equal(code, ast.Call, latex)


@pytest.mark.parametrize(
    ("code", "latex"),
    [
        ("pinv(A)", r"\mathbf{A}^{\dagger}"),
        ("pinv(b)", r"\mathbf{b}^{\dagger}"),
        ("pinv([[1, 2], [3, 4]])", r"\begin{bmatrix} 1 & 2 \\ 3 & 4 \end{bmatrix}^{\dagger}"),
        (
            "pinv([[1, 2, 3], [4, 5, 6], [7, 8, 9]])",
            r"\begin{bmatrix} 1 & 2 & 3 \\ 4 & 5 & 6 \\ 7 & 8 & 9 \end{bmatrix}^{\dagger}",
        ),
    ],
)
def test_pinv(code: str, latex: str) -> None:
    assert_expr_equal(code, ast.Call, latex)


@pytest.mark.parametrize(
    ("code", "latex"),
    [
        ("pinv()", r"\mathrm{pinv} \mathopen{}\left( \mathclose{}\right)"),
        ("pinv(2)", r"\mathrm{pinv} \mathopen{}\left( 2 \mathclose{}\right)"),
        (
            "pinv(a, (1, 0))",
            r"\mathrm{pinv} \mathopen{}\left( a, " r"\mathopen{}\left( 1, 0 \mathclose{}\right) \mathclose{}\right)",
        ),
    ],
)
def test_pinv_unsupported(code: str, latex: str) -> None:
    assert_expr_equal(code, ast.Call, latex)
