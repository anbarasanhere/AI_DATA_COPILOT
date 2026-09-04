from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _node(node_id: str, node_type: str, name: str, **properties: Any) -> dict[str, Any]:
    return {"id": node_id, "type": node_type, "name": name, "properties": properties}


def build_knowledge_graph(
    metadata: dict[str, Any],
    relationships: dict[str, Any],
    validation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic schema graph from generated discovery artifacts."""
    database = str(metadata.get("database", "unknown"))
    database_id = f"database:{database}"
    nodes = [_node(database_id, "database", database, source="database_metadata.json")]
    edges: list[dict[str, Any]] = []
    table_ids: set[str] = set()
    validation_by_key = {
        (
            item["from_table"],
            tuple(item.get("from_columns", [])),
            item["to_table"],
            tuple(item.get("to_columns", [])),
        ): item
        for item in (validation or {}).get("relationships", [])
    }

    for table in metadata.get("tables", []):
        table_name = str(table["name"])
        table_id = f"table:{database}:{table_name}"
        table_ids.add(table_id)
        nodes.append(
            _node(
                table_id,
                "table",
                table_name,
                database=database,
                comment=table.get("comment") or "",
                source="database_metadata.json",
            )
        )
        edges.append({"source": database_id, "target": table_id, "type": "contains"})
        for column in table.get("columns", []):
            column_name = str(column["COLUMN_NAME"])
            column_id = f"column:{database}:{table_name}:{column_name}"
            nodes.append(
                _node(
                    column_id,
                    "column",
                    column_name,
                    table=table_name,
                    data_type=column.get("COLUMN_TYPE") or column.get("DATA_TYPE"),
                    comment=column.get("COLUMN_COMMENT") or "",
                    source="database_metadata.json",
                )
            )
            edges.append({"source": table_id, "target": column_id, "type": "has_column"})

    for relationship in relationships.get("relationships", []):
        from_table = relationship["from_table"]
        to_table = relationship["to_table"]
        key = (
            from_table,
            tuple(relationship.get("from_columns", [])),
            to_table,
            tuple(relationship.get("to_columns", [])),
        )
        checked = validation_by_key.get(key, {})
        edges.append(
            {
                "source": f"table:{database}:{from_table}",
                "target": f"table:{database}:{to_table}",
                "type": "related_to",
                "properties": {
                    "from_columns": relationship.get("from_columns", []),
                    "to_columns": relationship.get("to_columns", []),
                    "status": checked.get("status", "unvalidated"),
                    "source": "relationships.json",
                },
            }
        )

    return {
        "version": 1,
        "database": database,
        "nodes": nodes,
        "edges": edges,
        "stats": {"nodes": len(nodes), "edges": len(edges), "tables": len(table_ids)},
    }


def write_knowledge_graph(graph: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
