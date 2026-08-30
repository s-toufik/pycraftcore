from abc import ABC, abstractmethod
from typing import Any


class Reader(ABC):
    @staticmethod
    @abstractmethod
    def read(file_path: str) -> Any: ...
