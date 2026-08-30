from dataclasses import asdict
from typing import TypeVar, Type

T = TypeVar("T")


class DictionarySerializer:
    @staticmethod
    def serialize(inputs: T) -> dict:
        return asdict(inputs)

    @staticmethod
    def deserialize(inputs: dict, cls: Type[T]) -> T:
        return cls(**inputs)
