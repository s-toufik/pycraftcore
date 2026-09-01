from collections.abc import Sequence
from typing import Any

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
        self._validate_window(window)

        if len(sequence) < window:
            return self._empty_array()

        array = self._as_array(sequence)
        kernel = np.full(window, 1.0 / window, dtype=np.float64)
        return np.convolve(array, kernel, mode="valid")

    def rolling_standard_deviation(
        self, sequence: Sequence[Numeric], window: int = 5
    ) -> np.ndarray:
        self._validate_window(window)

        if len(sequence) < window:
            return self._empty_array()

        array = self._as_array(sequence)

        return np.array([np.std(array[i : i + window]) for i in range(len(array) - window + 1)])

    @staticmethod
    def _validate_window(window: int) -> None:
        if window <= 0:
            raise ValueError("window must be strictly positive")

    @staticmethod
    def _empty_array() -> np.ndarray:
        return np.array([], dtype=np.float64)

    @staticmethod
    def _as_array(sequence: Sequence[Any]) -> np.ndarray:
        if isinstance(sequence, np.ndarray):
            return sequence
        return np.asarray(sequence, dtype=np.float64)
