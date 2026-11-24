from tests.application_configuration.model.connectors import a2a_connector


def test_an_a2a_connector_speaks_json_rpc_by_default():
    connector = a2a_connector()

    assert connector.binding == "JSONRPC"
    assert connector.certificate is None
