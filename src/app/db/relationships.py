from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection

from app.db.introspection import quote_identifier


def _columns_match(left: list[str], right: list[str]) -> str:
    return " AND ".join(
        f"child.{quote_identifier(child_column)} = parent.{quote_identifier(parent_column)}"
        for parent_column, child_column in zip(left, right, strict=True)
    )


def validate_relationships(
    connection: Connection,
    relationships: list[dict[str, Any]],
    available_tables: dict[str, set[str]],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for relationship in relationships:
        parent_table = relationship["from_table"]
        child_table = relationship["to_table"]
        parent_columns = relationship["from_columns"]
        child_columns = relationship["to_columns"]
        result: dict[str, Any] = {**relationship}
        missing = []
        if parent_table not in available_tables:
            missing.append(parent_table)
        if child_table not in available_tables:
            missing.append(child_table)
        if missing:
            result.update({"status": "missing_table", "missing_tables": missing})
            results.append(result)
            continue
        missing_columns = [
            f"{parent_table}.{column}"
            for column in parent_columns
            if column not in available_tables[parent_table]
        ] + [
            f"{child_table}.{column}"
            for column in child_columns
            if column not in available_tables[child_table]
        ]
        if missing_columns:
            result.update({"status": "missing_column", "missing_columns": missing_columns})
            results.append(result)
            continue

        parent = quote_identifier(parent_table)
        child = quote_identifier(child_table)
        join = _columns_match(parent_columns, child_columns)
        child_key = ", ".join(f"child.{quote_identifier(column)}" for column in child_columns)
        parent_key = ", ".join(f"parent.{quote_identifier(column)}" for column in parent_columns)
        query = text(
            f"""SELECT
                (SELECT COUNT(*) FROM {child}) AS child_rows,
                (SELECT COUNT(*) FROM {child} WHERE {" OR ".join(f"{quote_identifier(column)} IS NULL" for column in child_columns)}) AS null_child_rows,
                (SELECT COUNT(*) FROM {child} AS child
                 WHERE NOT EXISTS (
                     SELECT 1 FROM {parent} AS parent WHERE {join}
                 ) AND NOT ({" OR ".join(f"child.{quote_identifier(column)} IS NULL" for column in child_columns)})) AS orphan_child_rows,
                (SELECT COUNT(*) FROM (
                    SELECT {parent_key} FROM {parent} AS parent
                    GROUP BY {parent_key} HAVING COUNT(*) > 1
                ) AS duplicates) AS duplicate_parent_keys"""
        )
        values = connection.execute(query).mappings().one()
        result.update(
            {
                "child_rows": int(values["child_rows"]),
                "null_child_rows": int(values["null_child_rows"]),
                "orphan_child_rows": int(values["orphan_child_rows"]),
                "duplicate_parent_keys": int(values["duplicate_parent_keys"]),
            }
        )
        result["status"] = (
            "valid"
            if not result["orphan_child_rows"] and not result["duplicate_parent_keys"]
            else "review"
        )
        results.append(result)
    return results
