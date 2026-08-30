from enum import Enum


class CircuitState(Enum):
    OPEN = "open"
    CLOSED = "close"
    HALF_OPEN = "half_open"
