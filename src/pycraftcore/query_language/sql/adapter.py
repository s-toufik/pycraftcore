from sqlglot import Expr, errors, ErrorLevel, parse

from pycraftcore.query_language.constants.allowed_root_statements import ALLOWED_ROOT_STATEMENTS
from pycraftcore.query_language.constants.forbidden_statements import FORBIDDEN_EXPRESSIONS


class SqlExpressionHandler:
    def __init__(self, expression: str, dialect: str) -> None:
        self._expression = expression
        self._dialect = dialect

    def parse(self) -> list[Expr]:
        try:
            expressions: list[Expr | None] = parse(
                self._expression, self._dialect, error_level=ErrorLevel.RAISE
            )
        except errors.SqlglotError as exception:
            raise ValueError("SQL Expression could not be parsed") from exception

        if not expressions or not all(expressions):
            raise ValueError("SQL Expression could not be parsed")

        return [expression for expression in expressions if expression is not None]

    def validate_safe_query(self, expressions: list[Expr] | None = None) -> None:
        checked: list[Expr] = expressions or self.parse()
        for expression in checked:
            if not isinstance(expression, ALLOWED_ROOT_STATEMENTS):
                raise ValueError(
                    f"SQL Expression contains forbidden statement: {type(expression).__name__}"
                )
            for node in expression.walk():
                if isinstance(node, FORBIDDEN_EXPRESSIONS):
                    raise ValueError(
                        f"SQL Expression contains forbidden statement: {type(node).__name__}"
                    )

    def transpile(self, expressions: list[Expr] | None = None) -> str:
        checked: list[Expr] = expressions or self.parse()
        self.validate_safe_query(checked)
        return ";\n".join(expression.sql(dialect=self._dialect) for expression in checked)