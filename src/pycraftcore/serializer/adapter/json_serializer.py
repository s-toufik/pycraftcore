import json
from dataclasses import asdict, is_dataclass
from typing import Any, TypeVar, Type

from pydantic import TypeAdapter

T = TypeVar("T")


class JSONSerializer:
    @staticmethod
    def serialize(inputs: Any) -> str:
        if not is_dataclass(inputs) or isinstance(inputs, type):
            raise TypeError("serialize expects a dataclass instance")
        return json.dumps(asdict(inputs))

    @staticmethod
    def deserialize(inputs: str, cls: Type[T]) -> T:
        return TypeAdapter(cls).validate_json(inputs)
