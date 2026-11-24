from tests.application_configuration.model.connectors import api_connector


def test_api_connector_defaults_certificate_to_none():
    assert api_connector().certificate is None
