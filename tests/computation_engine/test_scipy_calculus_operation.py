import numpy as np
import pytest

from pycraftcore.computation_engine.adapter.scipy_calculus_operation import (
    ScipyCalculusOperation,
)


@pytest.fixture
def op() -> ScipyCalculusOperation:
    return ScipyCalculusOperation()


def test_integrate_uses_trapezoid_rule(op):
    result = op.integrate([1.0, 1.0, 1.0], dx=1.0)

    assert result == pytest.approx(2.0)


def test_integrate_returns_a_float(op):
    result = op.integrate([0.0, 1.0, 4.0], dx=1.0)

    assert isinstance(result, float)


def test_interpolate_linear_recovers_original_points(op):
    result = op.interpolate([1.0, 2.0, 4.0], kind="linear")

    assert np.allclose(result, [1.0, 2.0, 4.0])


def test_interpolate_defaults_to_linear(op):
    result = op.interpolate([0.0, 2.0, 4.0])

    assert np.allclose(result, [0.0, 2.0, 4.0])
