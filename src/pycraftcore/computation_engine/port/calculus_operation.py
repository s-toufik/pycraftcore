from collections.abc import Sequence
from typing import Protocol

from pycraftcore.computation_engine.const_typing import Kind, Numeric


class CalculusOperation(Protocol):
    def integrate(self, sequence: Sequence[Numeric], dx: float) -> float: ...

    def interpolate(
        self, sequence: Sequence[Numeric], kind: Kind = "linear", num: int | None = None
    ) -> Sequence[Numeric]: ...
