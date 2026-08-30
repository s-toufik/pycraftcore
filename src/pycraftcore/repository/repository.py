from __future__ import annotations

from typing import Any, Protocol


class AsyncRepository(Protocol):
    async def execute(
        self,
        sql: str,
        parameters: tuple[Any, ...] = (),
    ) -> list[dict[str, Any]]: ...


class AsyncRepositoryFactory(Protocol):
    async def connection(self) -> Any: ...
    async def disconnect(self) -> None: ...
    async def connect(self) -> AsyncRepository: ...
