from pycraftcore.query_language.sql.adapter import SqlExpressionHandler
from pycraftcore.query_language.sql.factory import SqlHandlerFactory


def test_call_returns_sql_expression_handler():
    factory = SqlHandlerFactory()

    handler = factory("SELECT 1", "sqlite")

    assert isinstance(handler, SqlExpressionHandler)
    assert handler._expression == "SELECT 1"
    assert handler._dialect == "sqlite"
