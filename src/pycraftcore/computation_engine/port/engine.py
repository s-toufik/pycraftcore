from typing import Protocol

from pycraftcore.computation_engine.port.arithmetic_operation import (
    ArithmeticOperation,
)
from pycraftcore.computation_engine.port.calculus_operation import (
    CalculusOperation,
)


class Engine(Protocol):
    @property
    def arithmetic(self) -> ArithmeticOperation: ...

    @property
    def calculus(self) -> CalculusOperation: ...
