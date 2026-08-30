import math

import numpy as np
import pytest

from pycraftcore.computation_engine.adapter.numpy_arithmetic_operation import (
    NumPyArithmeticOperation,
)


@pytest.fixture
def op() -> NumPyArithmeticOperation:
    return NumPyArithmeticOperation()


def test_to_array_converts_sequence(op):
    result = op.to_array([1, 2, 3])

    assert isinstance(result, np.ndarray)
    assert result.dtype == np.float64
    assert list(result) == [1.0, 2.0, 3.0]


def test_to_array_passes_through_existing_ndarray(op):
    array = np.array([1.0, 2.0])

    result = op.to_array(array)

    assert result is array


def test_log_returns_below_two_elements_is_empty(op):
    result = op.log_returns([1.0])

    assert result.size == 0


def test_log_returns_computes_log_of_ratios(op):
    result = op.log_returns([1.0, 2.0, 4.0])

    assert np.allclose(result, [math.log(2.0), math.log(2.0)])


def test_log_returns_replaces_nonpositive_ratio_with_nan(op):
    result = op.log_returns([1.0, -1.0])

    assert np.isnan(result[0])


def test_rolling_average_below_window_is_empty(op):
    result = op.rolling_average([1.0, 2.0], window=5)

    assert result.size == 0


def test_rolling_average_convolves_with_uniform_kernel(op):
    result = op.rolling_average([1.0, 2.0, 3.0], window=1)

    assert np.allclose(result, [1.0, 2.0, 3.0])


def test_rolling_standard_deviation_below_window_is_empty(op):
    result = op.rolling_standard_deviation([1.0, 2.0], window=5)

    assert result.size == 0


def test_rolling_standard_deviation_matches_manual_computation(op):
    sequence = [1.0, 2.0, 3.0, 4.0, 5.0]
    window = 2

    result = op.rolling_standard_deviation(sequence, window=window)

    expected = [np.std(sequence[i : i + window]) for i in range(len(sequence) - window + 1)]
    assert np.allclose(result, expected)
