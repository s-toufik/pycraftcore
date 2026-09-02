from sqlglot import exp

from pycraftcore.query_language.constants.sql.allowed_sql_root_statements import (
    ALLOWED_SQL_ROOT_STATEMENTS,
)
from pycraftcore.query_language.constants.sql.forbidden_sql_statements import (
    FORBIDDEN_SQL_EXPRESSIONS,
)


def test_allowed_root_statements_contains_only_read_statements():
    assert set(ALLOWED_SQL_ROOT_STATEMENTS) == {
        exp.Select,
        exp.Union,
        exp.Intersect,
        exp.Except,
    }


def test_forbidden_expressions_contains_mutating_and_ddl_statements():
    assert exp.Insert in FORBIDDEN_SQL_EXPRESSIONS
    assert exp.Update in FORBIDDEN_SQL_EXPRESSIONS
    assert exp.Delete in FORBIDDEN_SQL_EXPRESSIONS
    assert exp.Drop in FORBIDDEN_SQL_EXPRESSIONS


def test_allowed_and_forbidden_sets_do_not_overlap():
    assert set(ALLOWED_SQL_ROOT_STATEMENTS).isdisjoint(set(FORBIDDEN_SQL_EXPRESSIONS))
