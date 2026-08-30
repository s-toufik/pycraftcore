from dataclasses import asdict
from typing import TypeVar, Type

import msgpack

T = TypeVar("T")


class BinarySerializer:
    @staticmethod
    def serialize(inputs: T) -> bytes:
        return msgpack.packb(asdict(inputs))

    @staticmethod
    def deserialize(inputs: bytes, cls: Type[T]) -> T:
        return cls(**msgpack.unpackb(inputs, raw=False))
