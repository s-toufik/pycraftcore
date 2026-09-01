from typing import Any, Protocol, TypeVar

T = TypeVar("T")


class AsyncHttpFactory(Protocol):
    async def start(self) -> None: ...
    async def close(self) -> None: ...
    def create_client(self) -> AsyncHttpClient: ...
    @property
    def resilient_client_instance(self) -> T: ...


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
