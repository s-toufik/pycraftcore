from unittest.mock import MagicMock

from pycraftcore.computation_engine.adapter.compute_engine import ComputeEngine
from pycraftcore.computation_engine.port.engine import Engine


def test_compute_engine_satisfies_the_engine_protocol():
    engine: Engine = ComputeEngine(arithmetic=MagicMock(), calculus=MagicMock())

    assert engine.arithmetic is not None
    assert engine.calculus is not None
