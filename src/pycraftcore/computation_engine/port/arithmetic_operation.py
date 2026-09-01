from collections.abc import Sequence
from typing import Any, Protocol, runtime_checkable

from pycraftcore.computation_engine.const_typing import Numeric


@runtime_checkable
class ArithmeticOperation[T](Protocol):
    def to_array(self, sequence: Sequence[Any]) -> T: ...

    def log_returns(self, sequence: Sequence[Numeric]) -> T: ...

    def rolling_average(self, sequence: Sequence[Numeric], window: int) -> T: ...

    def rolling_standard_deviation(self, sequence: Sequence[Numeric], window: int) -> T: ...
