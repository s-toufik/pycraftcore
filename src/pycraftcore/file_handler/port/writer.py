from abc import ABC, abstractmethod
from typing import Any


class Writer(ABC):
    @staticmethod
    @abstractmethod
    def write(file_path: str, data: Any) -> Any: ...
