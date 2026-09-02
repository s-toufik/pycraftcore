import aiohttp
import httpx
import pytest

from pycraftcore.http.policy.http_error_policy import (
    is_business_error,
    is_retryable,
    status_code,
)


def make_httpx_status_error(code: int) -> httpx.HTTPStatusError:
    request = httpx.Request("GET", "https://api.test.com/health")
    response = httpx.Response(code, request=request)
    return httpx.HTTPStatusError("error", request=request, response=response)


def make_aiohttp_status_error(code: int) -> aiohttp.ClientResponseError:
    return aiohttp.ClientResponseError(request_info=None, history=(), status=code)


@pytest.mark.parametrize("code", [500, 502, 503])
def test_status_code_extracts_from_httpx_error(code):
    assert status_code(make_httpx_status_error(code)) == code


@pytest.mark.parametrize("code", [404, 429])
def test_status_code_extracts_from_aiohttp_error(code):
    assert status_code(make_aiohttp_status_error(code)) == code


def test_status_code_returns_none_for_unrelated_exception():
    assert status_code(ValueError("boom")) is None


@pytest.mark.parametrize("code", [408, 425, 429, 500, 502, 503, 504])
def test_is_retryable_true_for_retryable_status_codes(code):
    assert is_retryable(make_httpx_status_error(code)) is True


@pytest.mark.parametrize("code", [400, 401, 403, 404, 409, 422])
def test_is_retryable_false_for_non_retryable_status_codes(code):
    assert is_retryable(make_httpx_status_error(code)) is False


@pytest.mark.parametrize(
    "exception",
    [
        httpx.TransportError("boom"),
        aiohttp.ClientConnectionError("boom"),
        aiohttp.ServerTimeoutError("boom"),
        TimeoutError("boom"),
    ],
)
def test_is_retryable_true_for_transport_exceptions(exception):
    assert is_retryable(exception) is True


def test_is_retryable_false_for_unrelated_exception():
    assert is_retryable(ValueError("boom")) is False


@pytest.mark.parametrize("code", [400, 401, 403, 404, 409, 422])
def test_is_business_error_true_for_non_retryable_4xx(code):
    assert is_business_error(make_httpx_status_error(code)) is True


@pytest.mark.parametrize("code", [408, 425, 429])
def test_is_business_error_false_for_retryable_4xx(code):
    assert is_business_error(make_httpx_status_error(code)) is False


@pytest.mark.parametrize("code", [500, 502, 503, 504])
def test_is_business_error_false_for_5xx(code):
    assert is_business_error(make_httpx_status_error(code)) is False


def test_is_business_error_false_for_unrelated_exception():
    assert is_business_error(ValueError("boom")) is False
