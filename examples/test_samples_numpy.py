import numpy as np
import pytest


def get_determinant(matrix) -> int:
    return np.linalg.det(matrix)


def multiply_two_matrices(matrix1, matrix2):
    return matrix1 * matrix2


sample_quadratic_matrix_list = [[3, -1, 0], [0, 5, -2], [-8, 6, 3]]
sample_quadratic_matrix_np = np.array(sample_quadratic_matrix_list)

sample_quadratic_matrix_list2 = [[-4, 0, 3], [1, -5, -4], [0, 0, 2]]
sample_quadratic_matrix_np2 = np.array(sample_quadratic_matrix_list2)


def test_determinant_of_matrix_is_of_correct_value():
    assert np.rint(get_determinant(sample_quadratic_matrix_list)) == 65
    assert np.rint(get_determinant(sample_quadratic_matrix_np)) == 65


def test_two_matrices_are_multiplied_correctly():
    expected = np.array([[-12, 0, 0], [0, -25, 8], [0, 0, 6]])
    actual = multiply_two_matrices(sample_quadratic_matrix_np, sample_quadratic_matrix_np2)
    assert (expected == actual).all()


def test_if_multiply_receives_lists_error_is_raised():
    with pytest.raises(TypeError):
        multiply_two_matrices(sample_quadratic_matrix_list, sample_quadratic_matrix_list2)
        multiply_two_matrices(sample_quadratic_matrix_np, sample_quadratic_matrix_list2)
        multiply_two_matrices(sample_quadratic_matrix_list, sample_quadratic_matrix_np2)
