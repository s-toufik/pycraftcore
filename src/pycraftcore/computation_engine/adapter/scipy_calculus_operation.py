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

    def interpolate(self, sequence: Sequence[Numeric], kind: Kind = "linear") -> Sequence[Numeric]:
        arr = self._to_array(sequence)
        x = np.arange(len(arr))
        f = interpolate.interp1d(x, arr, kind=kind)
        return f(x)
