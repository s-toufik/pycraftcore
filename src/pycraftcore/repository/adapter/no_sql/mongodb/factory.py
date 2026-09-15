import asyncio

from pymongo import MongoClient

from pycraftcore.repository.adapter.no_sql.mongodb.adapter import MongoRepository
from pycraftcore.repository.adapter.no_sql.mongodb.schema import MongoConnector
from pycraftcore.repository.port import AsyncRepository


class MongoRepositoryFactory:
    def __init__(self, settings: MongoConnector) -> None:
        self._settings = settings
        self._client: MongoClient | None = None
        self._repository: AsyncRepository | None = None

    async def connection(self) -> MongoClient:
        if self._client is None:
            self._client = MongoClient(self._connection_uri())
        return self._client

    async def connect(self) -> AsyncRepository:
        if self._repository is None:
            client = await self.connection()
            self._repository = MongoRepository(client, self._settings.default_name)
        return self._repository

    async def disconnect(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
            self._repository = None

    async def ping(self) -> None:
        client = self._client
        if client is None:
            client = await self.connection()
        await asyncio.to_thread(client.admin.command, "ping")

    def _connection_uri(self) -> str:
        if (username := self._settings.username) and (password := self._settings.password):
            return f"mongodb://{username}:{password}@{self._settings.host}:{self._settings.port}/?authSource=admin"

        return f"mongodb://{self._settings.host}:{self._settings.port}"
