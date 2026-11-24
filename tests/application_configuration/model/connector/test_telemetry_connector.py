from pycraftcore.application_configuration.enum.connector_type import ConnectorType
from pycraftcore.application_configuration.model import TelemetryConnector
from tests.application_configuration.model.connectors import NO_AUTH


def test_telemetry_connector_holds_host_and_port():
    connector = TelemetryConnector(
        name="otel", type=ConnectorType.telemetry, auth=NO_AUTH, host="collector", port=4317
    )

    assert connector.host == "collector"
    assert connector.port == 4317
