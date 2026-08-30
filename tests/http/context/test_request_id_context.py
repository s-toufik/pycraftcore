from pycraftcore.http.context.request_context import request_id_context


def test_defaults_to_none():
    assert request_id_context.get() is None


def test_set_and_get_round_trip():
    token = request_id_context.set("req-123")
    try:
        assert request_id_context.get() == "req-123"
    finally:
        request_id_context.reset(token)
