from sqlite3 import Row

from aiosqlite import Connection, connect

from pycraftcore.repository.port.repository import AsyncRepository
from pycraftcore.repository.adapter.sql.sqlite import SqliteRepository
from pycraftcore.repository.adapter.sql.sqlite.database_file import SqliteDatabaseFile
from pycraftcore.repository.adapter.sql.sqlite.pragmas import SQLITE_PRAGMAS
from pycraftcore.repository.adapter.sql.sqlite.schema import SqliteConnector


class SqliteRepositoryFactory:
    def __init__(self, settings: SqliteConnector):
        self._settings = settings
        self._file = SqliteDatabaseFile(settings.path, settings.database)
        self._client: Connection | None = None
        self._pool: list[Connection] | None = None
        self._repository: AsyncRepository | None = None

    async def connection(self) -> Connection:
        if self._client is None:
            self._client = await self._open_connection()

        return self._client

    async def connect(self) -> AsyncRepository:

        if self._repository is not None:
            return self._repository

        self._pool = [await self._open_connection() for _ in range(self._settings.max_pool_size)]
        self._repository = SqliteRepository(self._pool)
        return self._repository

    async def disconnect(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None

        if self._pool is not None:
            for connection in self._pool:
                await connection.close()
            self._pool = None
            self._repository = None

    async def _open_connection(self) -> Connection:
        client = await connect(str(self._file.prepare()))
        client.row_factory = Row

        for pragma in SQLITE_PRAGMAS:
            await client.execute(pragma)

        return client
