from dataclasses import is_dataclass
from typing import Any, TypeVar

import orjson
from pydantic import TypeAdapter

T = TypeVar("T")


class JSONSerializer:
    @staticmethod
    def serialize(inputs: Any) -> str:
        if not is_dataclass(inputs) or isinstance(inputs, type):
            raise TypeError("serialize expects a dataclass instance")
        return orjson.dumps(inputs).decode()

    @staticmethod
    def deserialize(inputs: str, cls: type[T]) -> T:
        return TypeAdapter(cls).validate_json(inputs)
