from sqlalchemy.ext.asyncio import AsyncEngine

from pycraftcore.repository.adapter.sql.sqlalchemy.adapter import SqlAlchemyRepository
from pycraftcore.repository.adapter.sql.sqlalchemy.engine_builder import SqlAlchemyEngineBuilder
from pycraftcore.repository.port.repository import AsyncRepository


class SqlAlchemyRepositoryFactory:
    def __init__(self, builder: SqlAlchemyEngineBuilder) -> None:
        self._builder = builder
        self._engine: AsyncEngine | None = None
        self._repository: AsyncRepository | None = None

    async def connection(self) -> AsyncEngine:
        if self._engine is None:
            self._engine = self._builder.build()
        return self._engine

    async def connect(self) -> AsyncRepository:
        if self._repository is None:
            self._repository = SqlAlchemyRepository(await self.connection())
        return self._repository

    async def disconnect(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._repository = None

    async def ping(self) -> None:
        engine = await self.connection()
        async with engine.connect() as connection:
            await connection.exec_driver_sql("SELECT 1")
