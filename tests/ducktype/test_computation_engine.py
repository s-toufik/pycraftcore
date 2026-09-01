import numpy as np

from pycraftcore.computation_engine.adapter.compute_engine import ComputeEngine
from pycraftcore.computation_engine.adapter.numpy_arithmetic_operation import (
    NumPyArithmeticOperation,
)
from pycraftcore.computation_engine.adapter.scipy_calculus_operation import (
    ScipyCalculusOperation,
)
from pycraftcore.computation_engine.port.arithmetic_operation import ArithmeticOperation
from pycraftcore.computation_engine.port.calculus_operation import CalculusOperation
from pycraftcore.computation_engine.port.engine import Engine


def test_numpy_arithmetic_operation_satisfies_arithmetic_operation():
    operation: ArithmeticOperation[np.ndarray] = NumPyArithmeticOperation()

    assert isinstance(operation, ArithmeticOperation)


def test_scipy_calculus_operation_satisfies_calculus_operation():
    operation: CalculusOperation[np.ndarray] = ScipyCalculusOperation()

    assert isinstance(operation, CalculusOperation)


def test_compute_engine_satisfies_engine():
    engine: Engine[np.ndarray] = ComputeEngine(
        arithmetic=NumPyArithmeticOperation(),
        calculus=ScipyCalculusOperation(),
    )

    assert isinstance(engine, Engine)
