from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from pycraftcore.computation_engine.const_typing import Kind, Numeric


@runtime_checkable
class CalculusOperation[T](Protocol):
    def integrate(self, sequence: Sequence[Numeric], dx: float) -> float: ...

    def interpolate(
        self, sequence: Sequence[Numeric], kind: Kind = "linear", num: int | None = None
    ) -> T: ...
