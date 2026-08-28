from __future__ import annotations

import re
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection

_IDENTIFIER = re.compile(r"^[A-Za-z0-9_$]+$")


def quote_identifier(identifier: str) -> str:
    if not _IDENTIFIER.fullmatch(identifier):
        raise ValueError(f"Unsupported MySQL identifier: {identifier!r}")
    return f"`{identifier}`"


def inspect_database(
    connection: Connection, database: str, max_tables: int, sample_rows: int
) -> dict[str, Any]:
    tables = (
        connection.execute(
            text("""
            SELECT TABLE_NAME, TABLE_TYPE, TABLE_ROWS, ENGINE, TABLE_COMMENT
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = :database
            ORDER BY TABLE_NAME
            LIMIT :max_tables
        """),
            {"database": database, "max_tables": max_tables},
        )
        .mappings()
        .all()
    )

    result: dict[str, Any] = {"database": database, "tables": []}
    for table in tables:
        table_name = str(table["TABLE_NAME"])
        columns = (
            connection.execute(
                text("""
                SELECT COLUMN_NAME, ORDINAL_POSITION, DATA_TYPE, COLUMN_TYPE,
                       IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = :database AND TABLE_NAME = :table_name
                ORDER BY ORDINAL_POSITION
            """),
                {"database": database, "table_name": table_name},
            )
            .mappings()
            .all()
        )
        indexes = (
            connection.execute(
                text("""
                SELECT INDEX_NAME, COLUMN_NAME, NON_UNIQUE, SEQ_IN_INDEX
                FROM information_schema.STATISTICS
                WHERE TABLE_SCHEMA = :database AND TABLE_NAME = :table_name
                ORDER BY INDEX_NAME, SEQ_IN_INDEX
            """),
                {"database": database, "table_name": table_name},
            )
            .mappings()
            .all()
        )
        foreign_keys = (
            connection.execute(
                text("""
                SELECT CONSTRAINT_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME,
                       REFERENCED_COLUMN_NAME
                FROM information_schema.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = :database AND TABLE_NAME = :table_name
                  AND REFERENCED_TABLE_NAME IS NOT NULL
                ORDER BY CONSTRAINT_NAME, ORDINAL_POSITION
            """),
                {"database": database, "table_name": table_name},
            )
            .mappings()
            .all()
        )

        samples: list[dict[str, Any]] = []
        if sample_rows:
            query = text(f"SELECT * FROM {quote_identifier(table_name)} LIMIT :sample_rows")
            samples = [
                dict(row)
                for row in connection.execute(query, {"sample_rows": sample_rows}).mappings()
            ]

        profiles: list[dict[str, Any]] = []
        for column in columns:
            column_name = str(column["COLUMN_NAME"])
            profile_query = text(
                f"""SELECT COUNT(*) AS row_count,
                    SUM({quote_identifier(column_name)} IS NULL) AS null_count,
                    COUNT(DISTINCT {quote_identifier(column_name)}) AS distinct_count
                FROM {quote_identifier(table_name)}"""
            )
            profile = connection.execute(profile_query).mappings().one()
            profiles.append({"column": column_name, **dict(profile)})

        result["tables"].append(
            {
                "name": table_name,
                "type": table["TABLE_TYPE"],
                "row_count_estimate": table["TABLE_ROWS"],
                "engine": table["ENGINE"],
                "comment": table["TABLE_COMMENT"],
                "columns": [dict(column) for column in columns],
                "indexes": [dict(index) for index in indexes],
                "foreign_keys": [dict(key) for key in foreign_keys],
                "sample_rows": samples,
                "profiles": profiles,
            }
        )
    return result


def render_markdown(metadata: dict[str, Any]) -> str:
    lines = [
        f"# Database Schema: `{metadata['database']}`",
        "",
        "Generated from read-only MySQL introspection.",
        "",
    ]
    for table in metadata["tables"]:
        lines.extend(
            [
                f"## `{table['name']}`",
                "",
                f"- Type: `{table['type']}`",
                f"- Estimated rows: `{table['row_count_estimate']}`",
                "",
                "| Column | Type | Nullable | Nulls | Distinct | Key | Description |",
                "|---|---|---|---:|---:|---|---|",
            ]
        )
        primary_columns = {
            index["COLUMN_NAME"] for index in table["indexes"] if index["INDEX_NAME"] == "PRIMARY"
        }
        profiles = {profile["column"]: profile for profile in table["profiles"]}
        for column in table["columns"]:
            key = "PRIMARY KEY" if column["COLUMN_NAME"] in primary_columns else ""
            description = str(column["COLUMN_COMMENT"] or "").replace("|", "\\|")
            profile = profiles[column["COLUMN_NAME"]]
            lines.append(
                f"| `{column['COLUMN_NAME']}` | `{column['COLUMN_TYPE']}` | {column['IS_NULLABLE']} | {profile['null_count']} | {profile['distinct_count']} | {key} | {description} |"
            )
        if table["foreign_keys"]:
            lines.extend(["", "Foreign keys:"])
            for key in table["foreign_keys"]:
                lines.append(
                    f"- `{key['COLUMN_NAME']}` -> `{key['REFERENCED_TABLE_NAME']}.{key['REFERENCED_COLUMN_NAME']}`"
                )
        lines.append("")
    return "\n".join(lines)
