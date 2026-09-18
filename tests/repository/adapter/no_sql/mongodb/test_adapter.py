from unittest.mock import MagicMock

import pytest

from pycraftcore.repository.adapter.no_sql.mongodb.adapter import MongoRepository


@pytest.fixture
def fake_database():
    database = MagicMock()
    database.name = "app"
    return database


@pytest.fixture
def fake_client(fake_database):
    client = MagicMock()
    client.__getitem__.return_value = fake_database
    return client


@pytest.fixture
def repository(fake_client):
    return MongoRepository(fake_client, "app")


@pytest.mark.asyncio
async def test_execute_raises_when_query_is_not_valid_json(repository):
    with pytest.raises(ValueError, match="could not be parsed"):
        await repository.execute("not json")


@pytest.mark.asyncio
async def test_execute_raises_when_query_is_not_a_json_object(repository):
    with pytest.raises(ValueError, match="must be a json object"):
        await repository.execute("[1, 2, 3]")


@pytest.mark.asyncio
async def test_execute_returns_single_document_when_command_has_no_cursor(
    repository, fake_database
):
    fake_database.command.return_value = {"ok": 1.0}

    result = await repository.execute('{"ping": 1}')

    fake_database.command.assert_called_once_with({"ping": 1})
    assert result == [{"ok": 1.0}]


@pytest.mark.asyncio
async def test_execute_returns_first_batch_documents_from_cursor(repository, fake_database):
    fake_database.command.return_value = {
        "cursor": {
            "firstBatch": [{"_id": 1, "name": "John"}, {"_id": 2, "name": "Alice"}],
            "id": 0,
            "ns": "app.users",
        },
        "ok": 1.0,
    }

    result = await repository.execute('{"find": "users"}')

    assert result == [
        {"_id": "1", "name": "John"},
        {"_id": "2", "name": "Alice"},
    ]


@pytest.mark.asyncio
async def test_execute_follows_cursor_across_multiple_batches(repository, fake_database):
    fake_database.command.side_effect = [
        {
            "cursor": {
                "firstBatch": [{"_id": 1, "name": "John"}],
                "id": 42,
                "ns": "app.users",
            },
            "ok": 1.0,
        },
        {
            "cursor": {
                "nextBatch": [{"_id": 2, "name": "Alice"}],
                "id": 0,
            },
        },
    ]

    result = await repository.execute('{"find": "users"}')

    assert result == [
        {"_id": "1", "name": "John"},
        {"_id": "2", "name": "Alice"},
    ]
    second_call_command = fake_database.command.call_args_list[1].args[0]
    assert second_call_command == {"getMore": 42, "collection": "users"}


@pytest.mark.asyncio
async def test_execute_converts_object_id_to_string_only_when_present(repository, fake_database):
    fake_database.command.return_value = {"n": 1, "ok": 1.0}

    result = await repository.execute('{"update": "users"}')

    assert result == [{"n": 1, "ok": 1.0}]
