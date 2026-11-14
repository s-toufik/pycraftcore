from sqlalchemy import URL
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from pycraftcore.repository.adapter.sql.postgresql.schema import PostgresConnector

DRIVER: str = "postgresql+psycopg"


class PostgresEngineBuilder:
    def __init__(self, settings: PostgresConnector) -> None:
        self._settings = settings

    def build(self) -> AsyncEngine:
        return create_async_engine(
            self._url(),
            pool_size=self._settings.max_pool_size,
            max_overflow=0,
            pool_pre_ping=True,
        )

    def _url(self) -> URL:
        return URL.create(
            DRIVER,
            username=self._settings.user,
            password=self._settings.password,
            host=self._settings.host,
            port=self._settings.port,
            database=self._settings.default_name,
        )
