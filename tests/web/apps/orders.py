from collections.abc import AsyncIterator, Callable

from pycraftcore.web.actuator import Actuator

type Feed = Callable[[], AsyncIterator[bytes]]


class OutOfStock(Exception): ...


def orders_actuator(ready: bool) -> Actuator:
    return Actuator("orders-api", "1.2.3", "staging", "team@example.com", lambda: ready)


async def shipping(reference: str) -> AsyncIterator[bytes]:
    yield b"event: placed\ndata: 1\n\n"
    yield f"event: shipped\ndata: {reference}\n\n".encode()


async def one_tick() -> AsyncIterator[bytes]:
    yield b"event: tick\ndata: 1\n\n"
