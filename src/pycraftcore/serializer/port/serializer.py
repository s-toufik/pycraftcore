from typing import TypeVar, Type, Protocol

T = TypeVar("T")


class Serializer(Protocol):
    @staticmethod
    def serialize(inputs: T) -> bytes: ...

    @staticmethod
    def deserialize(inputs: bytes, cls: Type[T]) -> T: ...
