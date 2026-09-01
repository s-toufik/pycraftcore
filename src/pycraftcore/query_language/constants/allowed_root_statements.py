from sqlglot import exp

ALLOWED_ROOT_STATEMENTS: tuple[type[exp.Expression], ...] = (
    exp.Select,
    exp.Union,
    exp.Intersect,
    exp.Except,
)
