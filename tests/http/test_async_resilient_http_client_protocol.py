import pytest

from pycraftcore.http.port.async_resilient_http_client import AsyncResilientHttpClient


@pytest.mark.asyncio
async def test_resilient_client_satisfies_the_protocol_shape():
    class FakeResilientClient:
        async def get(self, *args, **kwargs):
            return "get"

        async def post(self, *args, **kwargs):
            return "post"

    client: AsyncResilientHttpClient = FakeResilientClient()

    assert await client.get() == "get"
    assert await client.post() == "post"
