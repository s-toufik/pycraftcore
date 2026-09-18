from unittest.mock import MagicMock

import pytest

from pycraftcore.http.context.request_context import request_id_context
from pycraftcore.telemetry.adapter.open_telemetry_tracer import OpenTelemetryTracer


def make_fake_otel_tracer():
    fake_span = MagicMock()
    fake_tracer = MagicMock()
    fake_tracer.start_as_current_span.return_value.__enter__.return_value = fake_span
    fake_tracer.start_as_current_span.return_value.__exit__.return_value = False
    return fake_tracer, fake_span


@pytest.mark.asyncio
async def test_trace_sets_ok_status_on_success():
    fake_tracer, fake_span = make_fake_otel_tracer()
    tracer = OpenTelemetryTracer(fake_tracer, "svc")

    @tracer.trace(span_name="op", static_attributes={"k": "v"})
    async def handler():
        return "result"

    result = await handler()

    assert result == "result"
    fake_span.set_status.assert_called_once()
    status = fake_span.set_status.call_args[0][0]
    assert status.status_code.name == "OK"


@pytest.mark.asyncio
async def test_trace_sets_error_status_and_reraises_on_failure():
    fake_tracer, fake_span = make_fake_otel_tracer()
    tracer = OpenTelemetryTracer(fake_tracer, "svc")

    @tracer.trace(span_name="op", static_attributes={})
    async def handler():
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        await handler()

    fake_span.set_status.assert_called_once()
    status = fake_span.set_status.call_args[0][0]
    assert status.status_code.name == "ERROR"


@pytest.mark.asyncio
async def test_trace_enriches_span_with_static_attributes():
    fake_tracer, fake_span = make_fake_otel_tracer()
    tracer = OpenTelemetryTracer(fake_tracer, "svc")

    @tracer.trace(span_name="op", static_attributes={"HttpMethod": "GET", "count": 3})
    async def handler():
        return None

    await handler()

    fake_span.set_attribute.assert_any_call("HttpMethod", "GET")
    fake_span.set_attribute.assert_any_call("count", "3")


@pytest.mark.asyncio
async def test_trace_enriches_span_with_request_id_when_set():
    fake_tracer, fake_span = make_fake_otel_tracer()
    tracer = OpenTelemetryTracer(fake_tracer, "svc")

    token = request_id_context.set("req-123")
    try:

        @tracer.trace(span_name="op", static_attributes={})
        async def handler():
            return None

        await handler()
    finally:
        request_id_context.reset(token)

    fake_span.set_attribute.assert_any_call("request_id", "req-123")
    fake_span.set_attribute.assert_any_call("tracer_name", "svc")


@pytest.mark.asyncio
async def test_trace_does_not_enrich_request_id_when_unset():
    fake_tracer, fake_span = make_fake_otel_tracer()
    tracer = OpenTelemetryTracer(fake_tracer, "svc")

    assert request_id_context.get() is None

    @tracer.trace(span_name="op", static_attributes={})
    async def handler():
        return None

    await handler()

    for call in fake_span.set_attribute.call_args_list:
        assert call.args[0] != "request_id"


@pytest.mark.asyncio
async def test_trace_preserves_wrapped_function_metadata():
    fake_tracer, _ = make_fake_otel_tracer()
    tracer = OpenTelemetryTracer(fake_tracer, "svc")

    @tracer.trace(span_name="op", static_attributes={})
    async def my_handler():
        return None

    assert my_handler.__name__ == "my_handler"
