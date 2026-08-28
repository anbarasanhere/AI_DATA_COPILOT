from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from app.db.config import get_settings
from app.db.connection import check_connection, create_mysql_engine, read_only_connection
from app.db.introspection import inspect_database, render_markdown


def json_default(value: object) -> object:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, bytes):
        return value.hex()
    return str(value)


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect a MySQL database without modifying it.")
    parser.add_argument(
        "--output-dir", default=None, help="Directory for JSON and Markdown reports"
    )
    args = parser.parse_args()

    settings = get_settings()
    output_dir = Path(args.output_dir or settings.mysql_output_dir)
    engine = create_mysql_engine(settings)
    try:
        database, version = check_connection(engine)
        if database.casefold() != settings.mysql_database.casefold():
            raise RuntimeError(f"Connected to {database!r}, expected {settings.mysql_database!r}")
        with read_only_connection(engine) as connection:
            metadata = inspect_database(
                connection, database, settings.mysql_max_tables, settings.mysql_sample_rows
            )
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "database_metadata.json").write_text(
            json.dumps({"mysql_version": version, **metadata}, indent=2, default=json_default)
            + "\n",
            encoding="utf-8",
        )
        (output_dir / "database_schema.md").write_text(render_markdown(metadata), encoding="utf-8")
        print(f"Connected to {database} (MySQL {version})")
        print(f"Discovered {len(metadata['tables'])} tables")
        print(f"Reports written to {output_dir}")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
