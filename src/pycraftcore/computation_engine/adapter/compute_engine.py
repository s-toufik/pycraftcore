from typing import Any

from pycraftcore.computation_engine.port.arithmetic_operation import (
    ArithmeticOperation,
)
from pycraftcore.computation_engine.port.calculus_operation import (
    CalculusOperation,
)


class ComputeEngine:
    def __init__(self, arithmetic: ArithmeticOperation[Any], calculus: CalculusOperation[Any]):
        self._arithmetic = arithmetic
        self._calculus = calculus

    @property
    def arithmetic(self) -> ArithmeticOperation[Any]:
        return self._arithmetic

    @property
    def calculus(self) -> CalculusOperation[Any]:
        return self._calculus
