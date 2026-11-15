from typing import Any

import pytest

from pycraftcore.repository.adapter.no_sql.mongodb.ttl_index import (
    MAX_EXPIRE_AFTER_SECONDS,
    MongoTtlIndex,
    TtlIndexChange,
)

HOUR = 3600
WEEK = 604800


class FakeDatabase:
    def __init__(self) -> None:
        self.commands: list[tuple[str, str, dict[str, Any]]] = []
        self.collections: dict[str, FakeCollection] = {}

    def command(self, command: str, name: str, **options: Any) -> dict[str, Any]:
        self.commands.append((command, name, options))
        change = options["index"]
        for index in self.collections[name].indexes:
            if index["key"] == change["keyPattern"]:
                index["expireAfterSeconds"] = change["expireAfterSeconds"]
        return {"ok": 1.0}


class FakeCollection:
    def __init__(self, database: FakeDatabase, name: str = "events") -> None:
        self.database = database
        self.name = name
        self.indexes: list[dict[str, Any]] = [{"key": {"_id": 1}, "name": "_id_"}]
        self.created: list[tuple[list[tuple[str, int]], dict[str, Any]]] = []
        database.collections[name] = self

    def list_indexes(self) -> list[dict[str, Any]]:
        return [dict(index) for index in self.indexes]

    def create_index(self, keys: list[tuple[str, int]], **options: Any) -> str:
        key = dict(keys)
        self.created.append((keys, options))
        self.indexes.append({"key": key, "name": f"{keys[0][0]}_1", **options})
        return f"{keys[0][0]}_1"

    def ttl(self, field: str) -> int | None:
        for index in self.indexes:
            if list(index["key"]) == [field]:
                return index.get("expireAfterSeconds")
        return None


@pytest.fixture
def collection() -> FakeCollection:
    return FakeCollection(FakeDatabase())


@pytest.mark.asyncio
async def test_a_missing_index_is_created_with_the_expiry(collection) -> None:
    change = await MongoTtlIndex("created_at", WEEK).ensure(collection)

    assert change is TtlIndexChange.CREATED
    assert collection.created == [([("created_at", 1)], {"expireAfterSeconds": WEEK})]


@pytest.mark.asyncio
async def test_an_index_with_the_same_expiry_is_left_alone(collection) -> None:
    collection.create_index([("created_at", 1)], expireAfterSeconds=WEEK)

    change = await MongoTtlIndex("created_at", WEEK).ensure(collection)

    assert change is TtlIndexChange.UNCHANGED
    assert len(collection.created) == 1
    assert collection.database.commands == []


@pytest.mark.asyncio
async def test_another_expiry_is_changed_in_place_without_rebuilding_the_index(
    collection,
) -> None:
    collection.create_index([("created_at", 1)], expireAfterSeconds=HOUR)

    change = await MongoTtlIndex("created_at", WEEK).ensure(collection)

    assert change is TtlIndexChange.UPDATED
    assert collection.ttl("created_at") == WEEK
    assert collection.database.commands == [
        (
            "collMod",
            "events",
            {"index": {"keyPattern": {"created_at": 1}, "expireAfterSeconds": WEEK}},
        )
    ]
    assert len(collection.created) == 1


@pytest.mark.asyncio
async def test_a_plain_index_on_the_field_becomes_a_ttl_index(collection) -> None:
    collection.indexes.append({"key": {"created_at": -1}, "name": "created_at_-1"})

    change = await MongoTtlIndex("created_at", WEEK).ensure(collection)

    assert change is TtlIndexChange.UPDATED
    assert collection.database.commands[0][2]["index"]["keyPattern"] == {"created_at": -1}


@pytest.mark.asyncio
async def test_a_compound_index_starting_with_the_field_is_not_taken_for_it(collection) -> None:
    collection.indexes.append({"key": {"created_at": 1, "user": 1}, "name": "created_at_1_user_1"})

    change = await MongoTtlIndex("created_at", WEEK).ensure(collection)

    assert change is TtlIndexChange.CREATED


@pytest.mark.parametrize("seconds", [-1, MAX_EXPIRE_AFTER_SECONDS + 1])
def test_an_expiry_mongodb_would_refuse_is_rejected(seconds) -> None:
    with pytest.raises(ValueError, match="expire_after_seconds"):
        MongoTtlIndex("created_at", seconds)


def test_a_field_is_required() -> None:
    with pytest.raises(ValueError, match="needs a field"):
        MongoTtlIndex(" ", WEEK)
