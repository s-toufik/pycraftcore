import ssl
from collections.abc import Callable, Mapping
from functools import cached_property
from typing import Any, Self

import orjson
from httpx import (
    AsyncBaseTransport,
    AsyncClient,
    AsyncHTTPTransport,
    Limits,
    Request,
    Response,
    Timeout,
)

from pycraftcore.http.configuration.http_client_configuration import HttpClientSettings
from pycraftcore.http.enum.http_method import HttpMethod
from pycraftcore.http.port.async_http_client import AsyncHttpClient
from pycraftcore.logger.port.logger import Logger


class HttpxClientFactory:
    def __init__(
        self,
        http_client_settings: HttpClientSettings | None = None,
        logger: Logger | None = None,
        http_transport: AsyncBaseTransport | None = None,
    ) -> None:
        self._http_client_settings: HttpClientSettings = (
            http_client_settings or HttpClientSettings()
        )
        self._logger: Logger | None = logger
        self._http_transport: AsyncBaseTransport | None = http_transport

    async def __aenter__(self) -> Self:
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def start(self) -> None:
        _ = self._client_instance

    async def close(self) -> None:
        client: AsyncClient | None = self.__dict__.pop("_client_instance", None)
        if client is not None and not client.is_closed:
            await client.aclose()

    def create_client(self) -> AsyncHttpClient:
        return HttpxClient(self._client_instance)

    @cached_property
    def _client_instance(self) -> AsyncClient:
        return AsyncClient(
            base_url=self._http_client_settings.client_params.base_url or "",
            timeout=self._timeout(),
            limits=self._limits(),
            transport=self._transport(),
            event_hooks=self._event_hooks(),
        )

    def _limits(self) -> Limits:
        return Limits(
            max_connections=self._http_client_settings.limits.max_connections,
            max_keepalive_connections=self._http_client_settings.limits.max_keepalive_connections,
            keepalive_expiry=self._http_client_settings.limits.keep_alive_timeout,
        )

    def _timeout(self) -> Timeout:
        return Timeout(self._http_client_settings.limits.timeout)

    def _transport(self) -> AsyncBaseTransport:
        if self._http_transport is None:
            self._http_transport = AsyncHTTPTransport(
                retries=0, verify=self._create_ssl_from_certificate()
            )

        return self._http_transport

    def _event_hooks(self) -> dict[str, list[Any]] | None:
        hook_events = self._event()
        return {"request": hook_events} if hook_events else None

    def _create_ssl_from_certificate(self) -> bool | ssl.SSLContext:
        if certificate_path := self._http_client_settings.security.certificate:
            context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
            context.load_verify_locations(cafile=certificate_path)
            if tls_cipher_spec := self._http_client_settings.security.tls_cipher_spec:
                context.set_ciphers(tls_cipher_spec)
            return context

        return True

    def _event(self) -> list[Callable[..., Any]]:
        return [self._event_log]

    async def _event_log(self, request: Request) -> None:
        if self._logger:
            self._logger.info(f"Request {request.method} {request.url}")


class HttpxClient:
    def __init__(self, client: AsyncClient) -> None:
        self._client: AsyncClient = client

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        response: Response = await self._client.request(
            method=method, url=endpoint, params=params, json=json, headers=headers
        )
        response.raise_for_status()

        content_type: str = response.headers.get("content-type", "")
        if "json" in content_type:
            return orjson.loads(response.content)

        return response.text

    async def get(
        self,
        endpoint: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        return await self._request(HttpMethod.GET.value, endpoint, params=params, headers=headers)

    async def post(
        self,
        endpoint: str,
        *,
        body: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        return await self._request(HttpMethod.POST.value, endpoint, json=body, headers=headers)