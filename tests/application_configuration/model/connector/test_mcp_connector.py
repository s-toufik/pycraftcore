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


@pytest.mark.parametrize(
    ("failures", "delay"),
    [(0, 60.0), (1, 5.0), (2, 10.0), (3, 20.0), (4, 40.0), (5, 60.0), (9, 60.0)],
)
def test_the_refresh_waits_its_interval_then_backs_off_up_to_its_maximum(failures, delay) -> None:
    assert McpRefresh().delay_after(failures) == delay


def test_the_refresh_follows_its_configured_numbers() -> None:
    refresh = McpRefresh(interval=120, retry_delay=2, max_retry_delay=10)

    assert [refresh.delay_after(failures) for failures in range(6)] == [120, 2, 4, 8, 10, 10]
