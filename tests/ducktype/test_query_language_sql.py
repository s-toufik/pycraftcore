from pycraftcore.query_language.sql.adapter import SqlExpressionHandler
from pycraftcore.query_language.sql.factory import SqlHandlerFactory
from pycraftcore.query_language.sql.sql_handler import SqlFactory, SqlHandler


def test_sql_handler_factory_satisfies_sql_factory():
    factory: SqlFactory = SqlHandlerFactory()

    assert isinstance(factory, SqlFactory)


def test_sql_expression_handler_satisfies_sql_handler():
    handler: SqlHandler = SqlExpressionHandler("SELECT * FROM users", "sqlite")

    assert isinstance(handler, SqlHandler)
