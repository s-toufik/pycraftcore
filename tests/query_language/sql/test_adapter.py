from unittest.mock import patch

import pytest
from sqlglot import exp

from pycraftcore.query_language.sql.adapter import SqlExpressionHandler


def test_parse_returns_expressions_for_valid_sql():
    handler = SqlExpressionHandler("SELECT * FROM users", "sqlite")

    expressions = handler.parse()

    assert len(expressions) == 1
    assert isinstance(expressions[0], exp.Select)


def test_parse_raises_value_error_for_invalid_sql():
    handler = SqlExpressionHandler("SELEKT *? FROM", "sqlite")

    with pytest.raises(ValueError, match="SQL Expression could not be parsed"):
        handler.parse()


def test_parse_raises_value_error_when_a_statement_parses_to_none():
    handler = SqlExpressionHandler("SELECT 1", "sqlite")

    with patch(
        "pycraftcore.query_language.sql.adapter.parse", return_value=[None]
    ), pytest.raises(ValueError, match="SQL Expression could not be parsed"):
        handler.parse()


def test_validate_safe_query_accepts_select():
    handler = SqlExpressionHandler("SELECT * FROM users", "sqlite")

    handler.validate_safe_query(handler.parse())


def test_validate_safe_query_accepts_union():
    handler = SqlExpressionHandler(
        "SELECT id FROM a UNION SELECT id FROM b", "sqlite"
    )

    handler.validate_safe_query(handler.parse())


def test_validate_safe_query_rejects_forbidden_root_statement():
    handler = SqlExpressionHandler("DROP TABLE users", "sqlite")

    with pytest.raises(ValueError, match="forbidden statement: Drop"):
        handler.validate_safe_query(handler.parse())


def test_validate_safe_query_rejects_insert_root_statement():
    handler = SqlExpressionHandler("INSERT INTO users VALUES (1)", "sqlite")

    with pytest.raises(ValueError, match="forbidden statement"):
        handler.validate_safe_query(handler.parse())


def test_validate_safe_query_rejects_forbidden_nested_node():
    handler = SqlExpressionHandler("SELECT * FROM users", "sqlite")
    expressions = handler.parse()
    expressions[0].set("limit", exp.Drop())

    with pytest.raises(ValueError, match="forbidden statement: Drop"):
        handler.validate_safe_query(expressions)


def test_validate_safe_query_parses_when_expressions_not_provided():
    handler = SqlExpressionHandler("SELECT * FROM users", "sqlite")

    handler.validate_safe_query(None)


def test_transpile_returns_sql_string_for_valid_query():
    handler = SqlExpressionHandler("SELECT * FROM users", "sqlite")

    result = handler.transpile()

    assert result == "SELECT * FROM users"


def test_transpile_joins_multiple_statements_with_semicolons():
    handler = SqlExpressionHandler("SELECT 1; SELECT 2", "sqlite")

    result = handler.transpile()

    assert result == "SELECT 1;\nSELECT 2"


def test_transpile_rejects_forbidden_statement():
    handler = SqlExpressionHandler("DELETE FROM users", "sqlite")

    with pytest.raises(ValueError, match="forbidden statement"):
        handler.transpile()
