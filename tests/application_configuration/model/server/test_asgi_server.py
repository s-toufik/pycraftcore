from pycraftcore.application_configuration.enum.server_type import ServerType
from pycraftcore.application_configuration.model import AsgiServer


def test_an_asgi_server_has_no_base_path_no_docs_no_cors_and_no_parameters_by_default():
    server = AsgiServer(name="orders-api", type=ServerType.asgi)

    assert server.base_path == ""
    assert server.docs is False
    assert server.cors_origins == []
    assert server.parameters == {}
