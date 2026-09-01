from dataclasses import asdict, is_dataclass
from typing import Any, TypeVar

from pydantic import TypeAdapter

T = TypeVar("T")


class DictionarySerializer:
    @staticmethod
    def serialize(inputs: Any) -> dict:
        if not is_dataclass(inputs) or isinstance(inputs, type):
            raise TypeError("serialize expects a dataclass instance")
        return asdict(inputs)

    @staticmethod
    def deserialize(inputs: dict, cls: type[T]) -> T:
        return TypeAdapter(cls).validate_python(inputs)
