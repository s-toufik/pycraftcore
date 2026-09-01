from typing import Sequence, Any

import numpy as np
from scipy import interpolate, integrate

from pycraftcore.computation_engine.const_typing import Numeric, Kind


class ScipyCalculusOperation:
    def _to_array(self, sequence: Sequence[Any]) -> np.ndarray:
        return np.asarray(sequence, dtype=np.float64)

    def integrate(self, sequence: Sequence[Numeric], dx: float) -> float:
        arr = self._to_array(sequence)
        return float(integrate.trapezoid(arr, dx=dx))

    def interpolate(
        self, sequence: Sequence[Numeric], kind: Kind = "linear", num: int | None = None
    ) -> Sequence[Numeric]:
        arr = self._to_array(sequence)
        if arr.size < 2:
            raise ValueError("interpolation requires at least two points")

        x = np.arange(arr.size)
        f = interpolate.interp1d(x, arr, kind=kind)
        return f(np.linspace(0, arr.size - 1, num or arr.size))