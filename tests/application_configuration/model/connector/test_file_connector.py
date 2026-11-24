from tests.application_configuration.model.connectors import file_connector


def test_file_connector_holds_base_path():
    assert file_connector().base_path == "/var/files"
