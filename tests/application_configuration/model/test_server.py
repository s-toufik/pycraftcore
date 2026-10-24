import pytest

from pycraftcore.application_configuration.enum.server_type import ServerType
from pycraftcore.application_configuration.model.server import AsgiServer, ServerRegistry
from pycraftcore.web.enum.web_framework import WebFramework


def orders_api() -> AsgiServer:
    return AsgiServer(name="orders-api", type=ServerType.asgi, framework=WebFramework.LITESTAR)


def test_an_asgi_server_has_no_base_path_no_cors_and_no_parameters_by_default():
    server = orders_api()

    assert server.base_path == ""
    assert server.cors_origins == []
    assert server.parameters == {}


def test_the_registry_returns_an_asgi_server_by_name():
    server = orders_api()
    registry = ServerRegistry({ServerType.asgi: {"orders-api": server}})

    assert registry.asgi("orders-api") is server
    assert registry[ServerType.asgi] == {"orders-api": server}


def test_an_unknown_server_name_is_a_key_error_naming_it():
    with pytest.raises(KeyError, match="no asgi server named 'billing-api'"):
        ServerRegistry().asgi("billing-api")


def test_an_empty_registry_has_no_server_of_any_type():
    assert ServerRegistry()[ServerType.asgi] == {}
