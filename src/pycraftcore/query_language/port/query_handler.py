from typing import Protocol, TypeVar, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class QueryFactory(Protocol):
    def __call__(self, expression: str, dialect: str) -> QueryHandler: ...


@runtime_checkable
class QueryHandler(Protocol):
    def transpile(self, expressions: T | None = None) -> str: ...
