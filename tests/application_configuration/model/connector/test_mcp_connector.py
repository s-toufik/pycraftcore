import pytest

from pycraftcore.application_configuration.model import McpRefresh
from tests.application_configuration.model.connectors import mcp_connector


def test_mcp_connector_defaults_transport_to_streamable_http_and_certificate_to_none():
    connector = mcp_connector()

    assert connector.transport == "streamable_http"
    assert connector.certificate is None


def test_mcp_connector_accepts_sse_transport():
    assert mcp_connector(transport="sse").transport == "sse"


def test_mcp_connector_defaults_its_refresh_settings():
    assert mcp_connector().refresh == McpRefresh(
        interval=60.0, retry_delay=5.0, max_retry_delay=60.0
    )


@pytest.mark.parametrize(
    ("settings", "message"),
    [
        ({"interval": 0}, "interval"),
        ({"retry_delay": 0}, "retry_delay"),
        ({"retry_delay": 10, "max_retry_delay": 5}, "max_retry_delay"),
    ],
)
def test_mcp_refresh_rejects_settings_that_cannot_schedule(settings, message):
    with pytest.raises(ValueError, match=message):
        McpRefresh(**settings)
