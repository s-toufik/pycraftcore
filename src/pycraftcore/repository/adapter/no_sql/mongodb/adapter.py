import asyncio
from typing import Any

import orjson
from pymongo import MongoClient


class MongoRepository:
    def __init__(self, mongo_client: MongoClient, database: str) -> None:
        self._database = mongo_client[database]

    async def execute(
        self,
        query: str,
        parameters: tuple[Any, ...] = (),
    ) -> list[dict[str, Any]]:
        command: dict[str, Any] = self._parse(query)
        return await asyncio.to_thread(self._run, command)

    @staticmethod
    def _parse(query: str) -> dict[str, Any]:
        try:
            command: Any = orjson.loads(query)
        except orjson.JSONDecodeError as exception:
            raise ValueError("Mongo query could not be parsed") from exception

        if not isinstance(command, dict):
            raise ValueError("Mongo query must be a json object")

        return command

    def _run(self, command: dict[str, Any]) -> list[dict[str, Any]]:
        result: dict[str, Any] = self._database.command(command)
        cursor: Any | None = result.get("cursor")

        if cursor is None:
            return [self._document(dict(result))]

        documents: list[dict[str, Any]] = [
            self._document(document) for document in cursor.get("firstBatch", [])
        ]
        cursor_id: Any = cursor.get("id", 0)
        collection: str = self._collection_name(cursor.get("ns", ""))

        while cursor_id:
            batch: dict[str, Any] = self._database.command(
                {
                    "getMore": cursor_id,
                    "collection": collection,
                }
            )
            next_cursor: Any = batch["cursor"]
            documents.extend(
                self._document(document) for document in next_cursor.get("nextBatch", [])
            )
            cursor_id = next_cursor.get("id", 0)

        return documents

    def _collection_name(self, namespace: str) -> str:
        prefix: str = f"{self._database.name}."
        if namespace.startswith(prefix):
            namespace = namespace[len(prefix) :]
        return namespace

    @staticmethod
    def _document(document: dict[str, Any]) -> dict[str, Any]:
        if "_id" in document:
            document["_id"] = str(document["_id"])
        return document
