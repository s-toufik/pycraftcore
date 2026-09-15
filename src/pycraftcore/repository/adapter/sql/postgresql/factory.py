from psycopg import AsyncConnection
from psycopg.conninfo import make_conninfo
from psycopg_pool import AsyncConnectionPool

from pycraftcore.repository.adapter.sql.postgresql.adapter import PostgresRepository
from pycraftcore.repository.adapter.sql.postgresql.schema import PostgresConnector
from pycraftcore.repository.port import AsyncRepository


class PostgresRepositoryFactory:
    def __init__(self, settings: PostgresConnector) -> None:
        self._settings = settings
        self._client: AsyncConnection | None = None
        self._pool: AsyncConnectionPool | None = None
        self._repository: AsyncRepository | None = None

    async def connection(self) -> AsyncConnection:
        if self._client is None:
            self._client = await AsyncConnection.connect(self._connection_information())
        return self._client

    async def connect(self) -> AsyncRepository:
        if self._repository is not None:
            return self._repository

        self._pool = AsyncConnectionPool(
            self._connection_information(),
            min_size=self._settings.min_pool_size,
            max_size=self._settings.max_pool_size,
            open=False,
        )
        await self._pool.open(wait=True)
        self._repository = PostgresRepository(self._pool)
        return self._repository

    async def disconnect(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None

        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            self._repository = None

    def _connection_information(self) -> str:
        return make_conninfo(
            host=self._settings.host,
            port=self._settings.port,
            dbname=self._settings.default_name,
            user=self._settings.user,
            password=self._settings.password,
        )
