from dataclasses import asdict, is_dataclass
from typing import Any, TypeVar

import msgpack
from pydantic import TypeAdapter

T = TypeVar("T")


class BinarySerializer:
    @staticmethod
    def serialize(inputs: Any) -> bytes:
        if not is_dataclass(inputs) or isinstance(inputs, type):
            raise TypeError("serialize expects a dataclass instance")
        return msgpack.packb(asdict(inputs))

    @staticmethod
    def deserialize(inputs: bytes, cls: type[T]) -> T:
        return TypeAdapter(cls).validate_python(msgpack.unpackb(inputs, raw=False))
