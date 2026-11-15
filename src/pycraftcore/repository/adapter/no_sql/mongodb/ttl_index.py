import asyncio
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from pymongo import ASCENDING
from pymongo.collection import Collection

MAX_EXPIRE_AFTER_SECONDS: int = 2_147_483_647


class TtlIndexChange(StrEnum):
    CREATED = "created"
    UPDATED = "updated"
    UNCHANGED = "unchanged"


@dataclass(frozen=True, slots=True)
class MongoTtlIndex:
    field: str
    expire_after_seconds: int

    def __post_init__(self) -> None:
        if not self.field.strip():
            raise ValueError("A TTL index needs a field")
        if not 0 <= self.expire_after_seconds <= MAX_EXPIRE_AFTER_SECONDS:
            raise ValueError(
                f"expire_after_seconds must be between 0 and {MAX_EXPIRE_AFTER_SECONDS}"
            )

    async def ensure(self, collection: Collection[Any]) -> TtlIndexChange:
        return await asyncio.to_thread(self._ensure, collection)

    def _ensure(self, collection: Collection[Any]) -> TtlIndexChange:
        index: dict[str, Any] | None = self._existing(collection)
        if index is None:
            collection.create_index(
                [(self.field, ASCENDING)], expireAfterSeconds=self.expire_after_seconds
            )
            return TtlIndexChange.CREATED
        if index.get("expireAfterSeconds") == self.expire_after_seconds:
            return TtlIndexChange.UNCHANGED
        collection.database.command(
            "collMod",
            collection.name,
            index={
                "keyPattern": dict(index["key"]),
                "expireAfterSeconds": self.expire_after_seconds,
            },
        )
        return TtlIndexChange.UPDATED

    def _existing(self, collection: Collection[Any]) -> dict[str, Any] | None:
        for index in collection.list_indexes():
            if list(dict(index["key"])) == [self.field]:
                return dict(index)
        return None
