from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta

from pycraftcore.application_configuration.enum import ConnectorType
from pycraftcore.application_configuration.model import McpConnector
from pycraftcore.authentication.model.no_auth import NoAuth
from pycraftcore.jwt.adapter import PyJwtTokens
from pycraftcore.mcp_sdk import create_app, create_server, mcp_path
from pycraftcore.web.schema import ApiSettings
from pycraftcore.web.middleware import BearerTokenMiddleware
from starlette.middleware import Middleware
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

API = ApiSettings(title="toolbox", version="1.3.0")
INITIALIZE = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "t", "version": "0"},
    },
}
ACCEPT = {"Accept": "application/json, text/event-stream"}


def connector(base_url: str = "http://localhost:8001/mcp") -> McpConnector:
    return McpConnector(
        name="self", type=ConnectorType.mcp, auth=NoAuth(), base_url=base_url, timeout=30
    )


def server(name: str = "toolbox"):
    return create_server(name=name, version="1.3.0")


def test_the_mcp_path_comes_from_the_connector_url_or_defaults_to_slash_mcp() -> None:
    assert mcp_path(connector("http://localhost:8001/custom/")) == "/custom"
    assert mcp_path(connector("http://localhost:8001")) == "/mcp"


def test_each_server_is_served_at_its_path() -> None:
    app = create_app(
        API, {"/mcp": server(), "/mcp/kitchen": server("toolbox-kitchen")}, connector()
    )

    with TestClient(app, base_url="http://localhost:8001") as client:
        everything = client.post("/mcp", json=INITIALIZE, headers=ACCEPT).json()
        kitchen = client.post("/mcp/kitchen", json=INITIALIZE, headers=ACCEPT).json()
        unknown = client.post("/mcp/travel", json=INITIALIZE, headers=ACCEPT)

    assert everything["result"]["serverInfo"]["name"] == "toolbox"
    assert kitchen["result"]["serverInfo"]["name"] == "toolbox-kitchen"
    assert unknown.status_code == 404


def test_only_the_connector_s_host_and_the_allowed_ones_are_accepted() -> None:
    app = create_app(API, {"/mcp": server()}, connector(), allowed_hosts=["sirius:8001"])

    with TestClient(app, base_url="http://localhost:8001") as client:
        statuses = [
            client.post("/mcp", json=INITIALIZE, headers=ACCEPT | {"Host": host}).status_code
            for host in ("localhost:8001", "sirius:8001", "elsewhere:8001")
        ]

    assert statuses == [200, 200, 421]


def test_its_own_routes_middleware_and_lifespan_come_with_the_servers() -> None:
    events: list[str] = []
    tokens = PyJwtTokens("k" * 32)

    @asynccontextmanager
    async def lifespan() -> AsyncIterator[None]:
        events.append("up")
        yield
        events.append("down")

    async def hello(_request) -> PlainTextResponse:
        return PlainTextResponse("hello")

    app = create_app(
        API,
        {"/mcp": server()},
        connector(),
        routes=[Route("/hello", hello)],
        middleware=[Middleware(BearerTokenMiddleware, verifier=tokens, protected=["/mcp"])],
        lifespan=lifespan,
    )
    bearer = {"Authorization": f"Bearer {tokens.issue('toufik', timedelta(hours=1))}"}

    with TestClient(app, base_url="http://localhost:8001") as client:
        hello_answer = client.get("/hello", headers={"X-Request-ID": "r1"})
        refused = client.post("/mcp", json=INITIALIZE, headers=ACCEPT)
        served = client.post("/mcp", json=INITIALIZE, headers=ACCEPT | bearer)

    assert (hello_answer.text, hello_answer.headers["x-request-id"]) == ("hello", "r1")
    assert (refused.status_code, served.status_code) == (401, 200)
    assert events == ["up", "down"]
