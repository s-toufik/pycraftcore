from typing import Protocol, runtime_checkable

from pycraftcore.computation_engine.port.arithmetic_operation import (
    ArithmeticOperation,
)
from pycraftcore.computation_engine.port.calculus_operation import (
    CalculusOperation,
)


@runtime_checkable
class Engine[T](Protocol):
    @property
    def arithmetic(self) -> ArithmeticOperation[T]: ...

    @property
    def calculus(self) -> CalculusOperation[T]: ...
