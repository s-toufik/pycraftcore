from typing import Sequence, Any, Protocol

from pycraftcore.computation_engine.const_typing import Numeric


class ArithmeticOperation(Protocol):
    def to_array(self, sequence: Sequence[Any]) -> Sequence[Any]: ...

    def log_returns(self, sequence: Sequence[Numeric]) -> Sequence[Numeric]: ...

    def rolling_average(self, sequence: Sequence[Numeric], window: int) -> Sequence[Numeric]: ...

    def rolling_standard_deviation(
        self, sequence: Sequence[Numeric], window: int
    ) -> Sequence[Numeric]: ...
