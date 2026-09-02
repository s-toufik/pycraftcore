from pycraftcore.query_language.adapter.sql import SqlExpressionHandler
from pycraftcore.query_language.adapter.sql import SqlHandlerFactory
from pycraftcore.query_language.port.query_handler import QueryFactory, QueryHandler


def test_sql_handler_factory_satisfies_sql_factory():
    factory: QueryFactory = SqlHandlerFactory()

    assert isinstance(factory, QueryFactory)


def test_sql_expression_handler_satisfies_sql_handler():
    handler: QueryHandler = SqlExpressionHandler("SELECT * FROM users", "sqlite")

    assert isinstance(handler, QueryHandler)
