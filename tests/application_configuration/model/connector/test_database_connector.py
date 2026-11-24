import pytest

from pycraftcore.application_configuration.model import DatabasePool
from tests.application_configuration.model.connectors import database_connector


def test_a_database_connector_waits_5_seconds_with_a_pool_of_one_by_default():
    connector = database_connector()

    assert connector.timeout == 5
    assert connector.pool == DatabasePool(min=1, max=1)


def test_a_database_connector_holds_its_pool():
    assert database_connector(pool=DatabasePool(min=2, max=4)).pool.max == 4


def test_a_database_timeout_must_be_positive():
    with pytest.raises(ValueError, match="timeout must be greater than 0"):
        database_connector(timeout=0)


@pytest.mark.parametrize(
    ("pool", "message"),
    [
        ({"min": -1}, "min must be 0 or more"),
        ({"max": 0}, "max must be 1 or more"),
        ({"min": 3, "max": 2}, "greater than or equal to min"),
    ],
)
def test_a_pool_that_cannot_work_is_refused(pool, message):
    with pytest.raises(ValueError, match=message):
        DatabasePool(**pool)
