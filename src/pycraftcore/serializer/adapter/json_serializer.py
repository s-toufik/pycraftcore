import json
from dataclasses import asdict
from typing import TypeVar, Type

T = TypeVar("T")


class JSONSerializer:
    @staticmethod
    def serialize(inputs: T) -> str:
        return json.dumps(asdict(inputs))

    @staticmethod
    def deserialize(inputs: str, cls: Type[T]) -> T:
        return cls(**json.loads(inputs))
