from pycraftcore.query_language.adapter.sql.adapter import SqlExpressionHandler
from pycraftcore.query_language.port.query_handler import QueryHandler


class SqlHandlerFactory:
    def __call__(self, expression: str, dialect: str) -> QueryHandler:
        return SqlExpressionHandler(expression, dialect)
