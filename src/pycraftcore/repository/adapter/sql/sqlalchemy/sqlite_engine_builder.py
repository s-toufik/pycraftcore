from typing import Any

from sqlalchemy import URL, event
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from pycraftcore.repository.adapter.sql.sqlite.database_file import SqliteDatabaseFile
from pycraftcore.repository.adapter.sql.sqlite.pragmas import SQLITE_PRAGMAS
from pycraftcore.repository.adapter.sql.sqlite.schema import SqliteConnector

DRIVER: str = "sqlite+aiosqlite"


class SqliteEngineBuilder:
    def __init__(self, settings: SqliteConnector) -> None:
        self._settings = settings
        self._file = SqliteDatabaseFile(settings.path, settings.database)

    def build(self) -> AsyncEngine:
        engine = create_async_engine(
            URL.create(DRIVER, database=str(self._file.prepare())),
            pool_size=self._settings.max_pool_size,
            max_overflow=0,
        )
        event.listen(engine.sync_engine, "connect", _apply_pragmas)
        return engine


def _apply_pragmas(dbapi_connection: Any, _record: Any) -> None:
    cursor = dbapi_connection.cursor()
    try:
        for pragma in SQLITE_PRAGMAS:
            cursor.execute(pragma)
    finally:
        cursor.close()
