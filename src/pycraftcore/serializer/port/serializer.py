from typing import Protocol, TypeVar, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class Serializer[W](Protocol):
    @staticmethod
    def serialize(inputs: T) -> W: ...

    @staticmethod
    def deserialize(inputs: W, cls: type[T]) -> T: ...
