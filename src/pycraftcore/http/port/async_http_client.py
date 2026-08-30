from typing import Protocol, Any, Optional, TypeVar

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
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> Any: ...
    async def post(
        self,
        endpoint: str,
        *,
        body: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> Any: ...
