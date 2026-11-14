from typing import Protocol, runtime_checkable

from sqlalchemy.ext.asyncio import AsyncEngine


@runtime_checkable
class SqlAlchemyEngineBuilder(Protocol):
    def build(self) -> AsyncEngine: ...
