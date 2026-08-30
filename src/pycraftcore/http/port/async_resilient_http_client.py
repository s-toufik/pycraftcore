from typing import Protocol, ParamSpec

P = ParamSpec("P")


class AsyncResilientHttpClient(Protocol):
    async def get(self, *args: P.args, **kwargs: P.kwargs): ...
    async def post(self, *args: P.args, **kwargs: P.kwargs): ...
