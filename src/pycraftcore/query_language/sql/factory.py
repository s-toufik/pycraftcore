from pycraftcore.query_language.sql.adapter import SqlExpressionHandler
from pycraftcore.query_language.sql.sql_handler import SqlHandler


class SqlHandlerFactory:
    def __call__(self, expression: str, dialect: str) -> SqlHandler:
        return SqlExpressionHandler(expression, dialect)
