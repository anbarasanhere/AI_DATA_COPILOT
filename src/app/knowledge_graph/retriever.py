from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class KnowledgeGraphRetriever:
    def __init__(self, graph_path: Path, metadata: dict[str, Any]) -> None:
        self.graph = json.loads(graph_path.read_text(encoding="utf-8"))
        self.metadata = metadata
        self.nodes = {node["id"]: node for node in self.graph.get("nodes", [])}
        self.edges = self.graph.get("edges", [])

    def retrieve(self, question: str, limit: int = 5) -> dict[str, Any]:
        tokens = set(re.findall(r"[a-z0-9_]+", question.casefold()))
        table_nodes = [node for node in self.nodes.values() if node["type"] == "table"]
        column_nodes = [node for node in self.nodes.values() if node["type"] == "column"]
        scores: dict[str, int] = {}
        for table in table_nodes:
            searchable = {table["name"].casefold()}
            searchable.update(
                node["name"].casefold()
                for node in column_nodes
                if node["properties"].get("table") == table["name"]
            )
            scores[table["id"]] = sum(
                2 if token == candidate else 1
                for token in tokens
                for candidate in searchable
                if token == candidate or token in candidate
            )

        matched = [node_id for node_id, score in scores.items() if score]
        matched.sort(key=lambda node_id: (-scores[node_id], self.nodes[node_id]["name"]))
        selected_ids = matched[:limit]
        matched_set = set(selected_ids)
        selected_set = set(selected_ids)
        for edge in self.edges:
            if edge["type"] == "related_to" and edge["source"] in matched_set:
                selected_set.add(edge["target"])
            elif edge["type"] == "related_to" and edge["target"] in matched_set:
                selected_set.add(edge["source"])

        table_by_name = {table["name"]: table for table in self.metadata.get("tables", [])}
        selected_tables = [
            table_by_name[self.nodes[node_id]["name"]]
            for node_id in selected_set
            if node_id in self.nodes and self.nodes[node_id]["name"] in table_by_name
        ]
        selected_tables.sort(key=lambda table: table["name"])
        selected_names = {table["name"] for table in selected_tables}
        graph_edges = [
            edge
            for edge in self.edges
            if edge["type"] == "related_to"
            and self.nodes[edge["source"]]["name"] in selected_names
            and self.nodes[edge["target"]]["name"] in selected_names
        ]
        relationships = [
            {
                "from_table": self.nodes[edge["source"]]["name"],
                "from_columns": edge["properties"]["from_columns"],
                "to_table": self.nodes[edge["target"]]["name"],
                "to_columns": edge["properties"]["to_columns"],
                "status": edge["properties"]["status"],
            }
            for edge in graph_edges
        ]
        return {
            "tables": selected_tables,
            "relationships": relationships,
            "graph_context": {
                "matched_tables": [self.nodes[node_id]["name"] for node_id in selected_ids],
                "expanded_tables": sorted(
                    selected_names - {self.nodes[node_id]["name"] for node_id in selected_ids}
                ),
                "relationship_edges": graph_edges,
                "source": "knowledge_graph.json",
            },
        }
