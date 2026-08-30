import ssl
from collections.abc import Callable, Mapping
from datetime import timedelta
from functools import cached_property
from types import CoroutineType
from typing import Any

import orjson
from aiobreaker import CircuitBreaker, CircuitBreakerListener, CircuitBreakerState
from httpx import (
    AsyncBaseTransport,
    AsyncClient,
    AsyncHTTPTransport,
    Limits,
    Request,
    Response,
    Timeout,
)
from tenacity import (
    AsyncRetrying,
    RetryCallState,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from pycraftcore.http.configuration.http_client_configuration import HttpClientSettings
from pycraftcore.http.enum.http_method import HttpMethod
from pycraftcore.http.port.async_http_client import AsyncHttpClient
from pycraftcore.logger.port.logger import Logger


class HttpxClientFactory:
    def __init__(self, http_client_settings: HttpClientSettings | None = None,
                 logger: Logger | None = None,
                 http_transport: AsyncBaseTransport | None = None) -> None:
        self._http_client_settings: HttpClientSettings = http_client_settings or HttpClientSettings()
        self._logger: Logger | None = logger
        self._http_transport: AsyncBaseTransport | None = http_transport

    async def __aenter__(self) -> HttpxClientFactory:
        _ = self._client_instance
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def start(self) -> None:
        ...
    async def close(self) -> None:
        if not self._client_instance.is_closed:
            await self._client_instance.aclose()

    def create_client(self) -> AsyncHttpClient:
        return HttpxClient(self._client_instance)

    @cached_property
    def _client_instance(self) -> AsyncClient:
        limits: Limits = Limits(
            max_connections=self._http_client_settings.limits.max_connections,
            max_keepalive_connections=self._http_client_settings.limits.max_keepalive_connections,
            keepalive_expiry=self._http_client_settings.limits.keep_alive_timeout
        )
        timeout: Timeout = Timeout(self._http_client_settings.limits.timeout)
        if not self._http_transport:
            self._http_transport: AsyncHTTPTransport = AsyncHTTPTransport(
                retries=self._http_client_settings.retry.retry_count,
                verify=self._create_ssl_from_certificate(),
            )

        hooks: dict[str, list[Any]] | None = None
        if hook_events:=self._event():
            hooks: dict[str, list[Any]] = {"request" : hook_events}

        client = AsyncClient(
            base_url=self._http_client_settings.client_params.base_url or "",
            timeout=timeout,
            limits=limits,
            transport=self._http_transport,
            event_hooks=hooks,
        )

        return client

    @property
    def resilient_client_instance(self) -> AsyncClient:
        return self._resilient_client_instance

    @cached_property
    def _resilient_client_instance(self) -> AsyncClient:
        limits: Limits = Limits(
            max_connections=self._http_client_settings.limits.max_connections,
            max_keepalive_connections=self._http_client_settings.limits.max_keepalive_connections,
            keepalive_expiry=self._http_client_settings.limits.keep_alive_timeout
        )
        timeout: Timeout = Timeout(self._http_client_settings.limits.timeout)
        if not self._http_transport:
            self._http_transport: AsyncHTTPTransport = AsyncHTTPTransport(
                retries=self._http_client_settings.retry.retry_count,
                verify=self._create_ssl_from_certificate(),
            )

        hooks: dict[str, list[Any]] | None = None
        if hook_events := self._event():
            hooks: dict[str, list[Any]] = {"request": hook_events}

        client = AsyncClient(
            base_url=self._http_client_settings.client_params.base_url or "",
            timeout=timeout,
            limits=limits,
            transport=ResilientTransport(
                http_client_settings=self._http_client_settings,
                logger=self._logger,
                transport=self._http_transport,
            )
        )
        return client

    def _create_ssl_from_certificate(self) -> bool | ssl.SSLContext:
        if certificate_path:=self._http_client_settings.security.certificate:
            context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
            context.load_verify_locations(cafile=certificate_path)
            if tls_cipher_spec:=self._http_client_settings.security.tls_cipher_spec:
                context.set_ciphers(tls_cipher_spec)
            return context
        return False

    def _event(self) -> list[Callable[..., CoroutineType[Any, Any, None]]]:
        return [self._event_log]

    async def _event_log(self, request: Request) -> None:
        counter: int = 0
        if self._logger:
            self._logger.info(f"Request #{counter}: {request.method} {request.url}")

class HttpxClient:

    def __init__(self, client: AsyncClient) -> None:
        self._client: AsyncClient = client

    async def _request(self, method: str, endpoint: str, *, params: Mapping[str, Any] | None = None, json: Mapping[str, Any] | None = None, headers: Mapping[str, str] | None = None) -> Any:
        response: Any = await self._client.request(method=method, url=endpoint, params=params, json=json, headers=headers)
        response.raise_for_status()
        if "application/json" in response.headers.get("content-type", None):
            return orjson.loads(response.text)

        return response.text

    async def get(self, endpoint: str, *, params: Mapping[str, Any] | None = None, headers: Mapping[str, str] | None = None) -> Any:
        return await self._request(HttpMethod.GET.value, endpoint, params=params, headers=headers)

    async def post(self, endpoint: str, *, body: Mapping[str, Any] | None = None, headers: Mapping[str, str] | None = None) -> Any:
        return await self._request(HttpMethod.POST.value, endpoint, json=body, headers=headers)

class BreakerLogger(CircuitBreakerListener):
    def __init__(self, logger: Logger | None = None) -> None:
        self._logger: Logger | None = logger
        self._last_exception : Exception | None = None

    def failure(self, breaker: CircuitBreaker, exception: Exception):
        self._last_exception: Exception = exception
        if self._logger:
            self._logger.warning(f"Circuit breaker failure {breaker.fail_counter}/{breaker.fail_max} recorded: {exception!r}")

    def success(self, breaker: CircuitBreaker) -> None:
        self._last_exception: Exception = None

    def state_change(self, breaker: CircuitBreaker, old: CircuitBreakerState, new: CircuitBreakerState) -> None:
        if self._logger:
            self._logger.info(f"Circuit breaker state change from {old.name} to {new.name}")
        if new == CircuitBreakerState.OPEN and self._logger:
            self._logger.error(f"Circuit breaker is OPEN - {breaker.fail_counter} consecutive failures reached "
                               f"over maximum failure threshold of {breaker.fail_max}. Last exception: {self._last_exception!r}. "
                               f"Breaker will reset in {breaker.timeout_duration.total_seconds():.1f} seconds.")


class ResilientTransport(AsyncBaseTransport):
    def __init__(self, http_client_settings: HttpClientSettings, logger: Logger | None = None, transport: AsyncBaseTransport | None = None) -> None:
        self._http_client_settings = http_client_settings or HttpClientSettings()
        self._logger: Logger | None = logger
        self._transport : AsyncBaseTransport = transport or AsyncBaseTransport()
        self._breaker_logger: BreakerLogger = BreakerLogger(logger)
        self._breaker: CircuitBreaker = CircuitBreaker(
            fail_max=self._http_client_settings.circuit_breaker.failure_threshold,
            timeout_duration=timedelta(self._http_client_settings.circuit_breaker.recovery_timeout),
            listeners=[self._breaker_logger]
        )
        self._retryer: AsyncRetrying = AsyncRetrying(
            retry=retry_if_exception_type(self._http_client_settings.retry.retry_on),
            stop=stop_after_attempt(self._http_client_settings.retry.retry_count),
            wait=wait_exponential(multiplier=self._http_client_settings.retry.retry_delay, min=1, max=8),
            reraise=True,
            before_sleep=self._log_retry)

    def _log_retry(self, retry_state: RetryCallState) -> None:
        exception = retry_state.outcome.exception()
        if self._logger:
            self._logger.warning(
                f"Retry #{retry_state.attempt_number} failed due to {exception!r}; "
                f"retrying in {retry_state.next_action.sleep:.1f} seconds..."
            )

    async def _retry_execute(self, request: Request) -> Response:
        return await self._retryer(self._transport.handle_async_request, request)

    async def handle_async_request(self, request: Request) -> Response:
        return await self._breaker.call_async(self._retry_execute, request)

    async def aclose(self) -> None:
        await self._transport.aclose()