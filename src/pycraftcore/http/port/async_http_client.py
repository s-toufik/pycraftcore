from typing import Any, Protocol, runtime_checkable, Self


@runtime_checkable
class AsyncHttpFactory(Protocol):

    async def start(self) -> None: ...
    async def close(self) -> None: ...
    def create_client(self) -> AsyncHttpClient: ...
    async def __aenter__(self) -> Self: ...
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None: ...

@runtime_checkable
class AsyncHttpClient(Protocol):
    async def get(
        self,
        endpoint: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any: ...
    async def post(
        self,
        endpoint: str,
        *,
        body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any: ...
