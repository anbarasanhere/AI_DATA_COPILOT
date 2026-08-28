from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.db.config import get_settings
from app.db.connection import create_mysql_engine, read_only_connection
from app.db.introspection import inspect_database
from app.db.relationships import validate_relationships


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate logical relationships against MySQL data."
    )
    parser.add_argument(
        "--relationship-file", type=Path, default=Path("metadata/relationships.json")
    )
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()

    settings = get_settings()
    output_dir = args.output_dir or Path(settings.mysql_output_dir)
    contract = json.loads(args.relationship_file.read_text(encoding="utf-8"))
    engine = create_mysql_engine(settings)
    try:
        with read_only_connection(engine) as connection:
            metadata = inspect_database(
                connection, settings.mysql_database, settings.mysql_max_tables, 0
            )
            available_tables = {
                table["name"]: {column["COLUMN_NAME"] for column in table["columns"]}
                for table in metadata["tables"]
            }
            results = validate_relationships(
                connection, contract.get("relationships", []), available_tables
            )
    finally:
        engine.dispose()

    output_dir.mkdir(parents=True, exist_ok=True)
    report = {"database": settings.mysql_database, "relationships": results}
    (output_dir / "relationship_validation.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    valid = sum(result["status"] == "valid" for result in results)
    review = sum(result["status"] == "review" for result in results)
    missing = len(results) - valid - review
    lines = [
        f"# Relationship Validation: `{settings.mysql_database}`",
        "",
        f"Validated `{len(results)}` logical relationships against live data.",
        "",
        "| Parent | Child | Null child keys | Orphan child rows | Duplicate parent keys | Status |",
        "|---|---|---:|---:|---:|---|",
    ]
    for result in results:
        lines.append(
            f"| `{result['from_table']}` | `{result['to_table']}` | {result.get('null_child_rows', '-')} | {result.get('orphan_child_rows', '-')} | {result.get('duplicate_parent_keys', '-')} | `{result['status']}` |"
        )
    lines.extend(["", f"Summary: `{valid}` valid, `{review}` review, `{missing}` missing.", ""])
    (output_dir / "relationship_validation.md").write_text("\n".join(lines), encoding="utf-8")
    print(
        f"Validated {len(results)} relationships: {valid} valid, {review} review, {missing} missing"
    )
    print(f"Reports written to {output_dir}")


if __name__ == "__main__":
    main()
