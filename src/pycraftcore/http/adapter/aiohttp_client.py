import ssl
from collections.abc import Mapping
from typing import Any, NoReturn, Self

import aiohttp
import orjson

from pycraftcore.http.configuration.http_client_configuration import HttpClientSettings
from pycraftcore.http.enum.http_method import HttpMethod
from pycraftcore.http.port.async_http_client import AsyncHttpClient


class AioHttpClient:
    __slots__ = ("_base_url", "_session")

    def __init__(self, base_url: str, session: aiohttp.ClientSession) -> None:

        self._session: aiohttp.ClientSession = session
        self._base_url: str = base_url

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:

        url: str = self._build_url(endpoint)

        async with self._session.request(
            method=method, url=url, params=params, json=json, headers=headers
        ) as response:
            response.raise_for_status()
            content_type: Any = response.headers.get("Content-Type", "")

            if "application/json" in content_type:
                return orjson.loads(await response.read())

            return await response.text()

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

    def _build_url(self, endpoint: str) -> str:
        if self._base_url:
            return self._base_url.rstrip("/") + "/" + endpoint.lstrip("/")
        else:
            return endpoint.lstrip("/")


class AioHttpClientFactory:
    def __init__(
        self,
        http_client_settings: HttpClientSettings | None = None,
        *,
        timeout: int | None = None,
        connector: aiohttp.BaseConnector | None = None,
    ) -> None:

        self._http_client_settings: HttpClientSettings = (
            http_client_settings or HttpClientSettings()
        )
        self._timeout: aiohttp.ClientTimeout = aiohttp.ClientTimeout(
            total=timeout or self._http_client_settings.limits.timeout
        )
        self._connector: aiohttp.BaseConnector | None = connector
        self._owns_connector: bool = connector is None

        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> Self:
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def start(self) -> None:
        await self._start_connector()
        await self._start_session()

    async def close(self) -> None:
        await self._close_session()
        await self._close_connector()
        self._session = None

    def create_client(self) -> AsyncHttpClient:
        session: aiohttp.ClientSession = self._ensure_session()
        return AioHttpClient(
            base_url=self._http_client_settings.client_params.base_url,
            session=session,
        )

    def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            raise RuntimeError(
                "Factory session is not started. Either use the context manager or start the factory before creating the client"
            )

        return self._session

    async def _close_session(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def _close_connector(self) -> None:
        if self._owns_connector and self._connector is not None:
            await self._connector.close()
            self._connector = None

    async def _start_session(self) -> None:
        self._session = aiohttp.ClientSession(
            timeout=self._timeout,
            connector=self._connector,
            connector_owner=self._owns_connector,
        )

    async def _start_connector(self) -> None:
        if self._owns_connector and self._connector is None:
            self._connector = aiohttp.TCPConnector(
                limit=self._http_client_settings.limits.max_connections,
                limit_per_host=self._http_client_settings.limits.max_connections_per_host,
                ttl_dns_cache=self._http_client_settings.limits.ttl_dns_cache,
                ssl=self._create_ssl_from_certificate(),
                keepalive_timeout=self._http_client_settings.limits.keep_alive_timeout,
            )

    def _create_ssl_from_certificate(self) -> bool | ssl.SSLContext:
        if certificate_path := self._http_client_settings.security.certificate:
            context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
            context.load_verify_locations(cafile=certificate_path)
            if tls_cipher_spec := self._http_client_settings.security.tls_cipher_spec:
                context.set_ciphers(tls_cipher_spec)
            return context
        return False

    @property
    def resilient_client_instance(self) -> NoReturn:
        raise NotImplementedError(
            "For aiohttp adapter compose the resilient client using the resilient implementation"
        )
