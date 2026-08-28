from dataclasses import dataclass

import sqlglot
from sqlglot import exp


@dataclass(frozen=True)
class SqlValidation:
    valid: bool
    normalized_sql: str | None = None
    error: str | None = None


def validate_read_only_sql(sql: str) -> SqlValidation:
    candidate = sql.strip()
    if not candidate:
        return SqlValidation(False, error="SQL must not be empty")
    try:
        statements = sqlglot.parse(candidate, read="mysql")
    except sqlglot.errors.ParseError as exc:
        return SqlValidation(False, error=f"SQL could not be parsed: {exc}")
    if len(statements) != 1:
        return SqlValidation(False, error="Multiple SQL statements are not allowed")
    statement = statements[0]
    if not isinstance(statement, (exp.Select, exp.Union)):
        return SqlValidation(False, error="Only SELECT or WITH queries are allowed")
    return SqlValidation(True, normalized_sql=statement.sql(dialect="mysql"))
