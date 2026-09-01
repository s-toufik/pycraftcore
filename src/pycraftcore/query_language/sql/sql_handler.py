from typing import Protocol, TypeVar, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class SqlFactory(Protocol):
    def __call__(self, expression: str, dialect: str) -> SqlHandler: ...


@runtime_checkable
class SqlHandler(Protocol):
    def transpile(self, expressions: T | None = None) -> str: ...
