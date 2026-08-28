from app.db.introspection import quote_identifier
from app.sql.validator import validate_read_only_sql


def test_quote_identifier_accepts_mysql_identifier() -> None:
    assert quote_identifier("orders_2026") == "`orders_2026`"


def test_quote_identifier_rejects_sql_expression() -> None:
    try:
        quote_identifier("orders; DROP TABLE users")
    except ValueError:
        return
    raise AssertionError("unsafe identifier was accepted")


def test_validator_allows_select_and_cte() -> None:
    assert validate_read_only_sql("SELECT * FROM product").valid
    assert validate_read_only_sql("WITH rows AS (SELECT 1) SELECT * FROM rows").valid


def test_validator_rejects_mutation_and_multiple_statements() -> None:
    assert not validate_read_only_sql("DROP TABLE product").valid
    assert not validate_read_only_sql("SELECT 1; SELECT 2").valid
