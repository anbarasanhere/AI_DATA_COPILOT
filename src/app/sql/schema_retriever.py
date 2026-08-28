from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class SchemaRetriever:
    def __init__(self, metadata_path: Path, relationship_path: Path | None = None) -> None:
        self.metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        self.relationships = (
            json.loads(relationship_path.read_text(encoding="utf-8"))
            if relationship_path and relationship_path.exists()
            else {"relationships": []}
        )

    def retrieve(self, question: str, limit: int = 5) -> dict[str, Any]:
        tokens = set(re.findall(r"[a-z0-9_]+", question.casefold()))
        scored: list[tuple[int, dict[str, Any]]] = []
        for table in self.metadata.get("tables", []):
            searchable = {table["name"].casefold()}
            searchable.update(
                column["COLUMN_NAME"].casefold() for column in table.get("columns", [])
            )
            score = sum(token in searchable or token in " ".join(searchable) for token in tokens)
            if score:
                scored.append((score, table))
        selected = [
            table
            for _, table in sorted(scored, key=lambda item: (-item[0], item[1]["name"]))[:limit]
        ]
        names = {table["name"] for table in selected}
        relationships = [
            relation
            for relation in self.relationships.get("relationships", [])
            if relation["from_table"] in names or relation["to_table"] in names
        ]
        return {"tables": selected, "relationships": relationships}
