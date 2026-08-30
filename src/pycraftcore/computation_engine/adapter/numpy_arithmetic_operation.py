from typing import Sequence, Any

import numpy as np

from pycraftcore.computation_engine.const_typing import Numeric


class NumPyArithmeticOperation:
    def to_array(self, sequence: Sequence[Any]) -> np.ndarray:
        return self._as_array(sequence)

    def log_returns(self, sequence: Sequence[Numeric]) -> np.ndarray:

        if len(sequence) < 2:
            return self._empty_array()

        array = self._as_array(sequence)

        ratio = array[1:] / array[:-1]
        ratio = np.where(ratio <= 0, np.nan, ratio)
        return np.log(ratio)

    def rolling_average(self, sequence: Sequence[Numeric], window: int = 5) -> np.ndarray:
        if len(sequence) < window:
            return self._empty_array()

        array = self._as_array(sequence)
        kernel = self._as_array((np.ones(window) / window).astype(np.float64))
        return np.convolve(array, kernel)

    def rolling_standard_deviation(
        self, sequence: Sequence[Numeric], window: int = 5
    ) -> np.ndarray:
        if len(sequence) < window:
            return self._empty_array()

        array = self._as_array(sequence)

        return np.array([np.std(array[i : i + window]) for i in range(len(array) - window + 1)])

    @staticmethod
    def _empty_array() -> np.ndarray:
        return np.array([], dtype=np.float64)

    @staticmethod
    def _as_array(sequence: Sequence[Any]) -> np.ndarray:
        if isinstance(sequence, np.ndarray):
            return sequence
        return np.asarray(sequence, dtype=np.float64)
