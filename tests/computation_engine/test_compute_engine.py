from unittest.mock import MagicMock

from pycraftcore.computation_engine.adapter.compute_engine import ComputeEngine


def test_exposes_injected_arithmetic_and_calculus():
    arithmetic = MagicMock()
    calculus = MagicMock()

    engine = ComputeEngine(arithmetic=arithmetic, calculus=calculus)

    assert engine.arithmetic is arithmetic
    assert engine.calculus is calculus
