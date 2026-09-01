from typing import Protocol, TypeVar

T = TypeVar("T")


class Serializer(Protocol):
    @staticmethod
    def serialize(inputs: T) -> bytes: ...

    @staticmethod
    def deserialize(inputs: bytes, cls: type[T]) -> T: ...
