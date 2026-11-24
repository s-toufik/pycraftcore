import pytest

from pycraftcore.application_configuration.enum.operation_type import OperationType
from pycraftcore.application_configuration.model import DatabaseOperation
from tests.application_configuration.model.connectors import database_connector


def make_database_operation(**overrides) -> DatabaseOperation:
    values = dict(
        name="orders",
        type=OperationType.database,
        connector=database_connector(engine="postgresql", host="db", port=5432),
        database="shop",
    )
    values.update(overrides)
    return DatabaseOperation(**values)


def test_a_database_operation_names_its_database_and_has_no_collections_or_ttl_by_default():
    operation = make_database_operation()

    assert operation.database == "shop"
    assert (operation.collections, operation.ttl, operation.parameters) == ({}, None, {})


def test_a_collection_is_found_by_its_role():
    operation = make_database_operation(collections={"events": "order_events"})

    assert operation.collection("events") == "order_events"


def test_a_missing_collection_names_the_operation_and_the_role():
    with pytest.raises(KeyError, match="'orders' has no collection 'events'"):
        make_database_operation().collection("events")


@pytest.mark.parametrize(
    ("overrides", "message"),
    [({"database": " "}, "needs a database"), ({"ttl": -1}, "ttl must be 0 or more")],
)
def test_a_database_operation_that_cannot_work_is_refused(overrides, message):
    with pytest.raises(ValueError, match=message):
        make_database_operation(**overrides)
