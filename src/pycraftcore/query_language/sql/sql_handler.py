from typing import Protocol, TypeVar

T = TypeVar("T")

class SqlFactory(Protocol):
    def __call__(self, expression: str, dialect: str) -> SqlHandler: ...

class SqlHandler(Protocol):
    def transpile(self, expressions: T = None) -> str: ...