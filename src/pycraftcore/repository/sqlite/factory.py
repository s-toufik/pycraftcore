from pathlib import Path
from sqlite3 import Row

from aiosqlite import Connection, connect

from pycraftcore.repository.repository import AsyncRepository
from pycraftcore.repository.sqlite.adapter import SqliteRepository
from pycraftcore.repository.sqlite.schema import SqliteConnector

_PRAGMAS: tuple[str, ...] = (
    "PRAGMA journal_mode=WAL",
    "PRAGMA busy_timeout=5000",
    "PRAGMA synchronous=NORMAL",
)


class SQLiteRepositoryFactory:
    def __init__(self, settings: SqliteConnector):
        self._settings = settings
        self._client: Connection | None = None
        self._pool: list[Connection] | None = None
        self._repository: AsyncRepository | None = None

    async def connection(self) -> Connection:
        if self._client is None:
            self._create_repository_directory(self._settings.path)
            self._client = await self._open_connection()

        return self._client

    async def connect(self) -> AsyncRepository:

        if self._repository is not None:
            return self._repository

        self._create_repository_directory(self._settings.path)
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
        client = await connect(
            self._set_repository_file(self._settings.path, self._settings.default_name)
        )
        client.row_factory = Row

        for pragma in _PRAGMAS:
            await client.execute(pragma)

        return client

    @staticmethod
    def _create_repository_directory(path: str) -> None:
        directory: Path = Path(path)
        directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _set_repository_file(path: str, repository_name: str = "sqlite") -> str:
        return str(Path(path) / f"{repository_name}.db")
