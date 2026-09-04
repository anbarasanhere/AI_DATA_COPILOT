from pathlib import Path

from app.knowledge_graph.graph import build_knowledge_graph, write_knowledge_graph
from app.knowledge_graph.retriever import KnowledgeGraphRetriever


def _artifacts() -> tuple[dict, dict, dict]:
    metadata = {
        "database": "market",
        "tables": [
            {
                "name": "vendor",
                "comment": "Market vendors",
                "columns": [{"COLUMN_NAME": "vendor_id", "COLUMN_TYPE": "int"}],
            },
            {
                "name": "purchases",
                "columns": [
                    {"COLUMN_NAME": "vendor_id", "COLUMN_TYPE": "int"},
                    {"COLUMN_NAME": "market_date", "COLUMN_TYPE": "date"},
                ],
            },
            {
                "name": "market_dates",
                "columns": [{"COLUMN_NAME": "market_date", "COLUMN_TYPE": "date"}],
            },
        ],
    }
    relationships = {
        "relationships": [
            {
                "from_table": "vendor",
                "from_columns": ["vendor_id"],
                "to_table": "purchases",
                "to_columns": ["vendor_id"],
            },
            {
                "from_table": "market_dates",
                "from_columns": ["market_date"],
                "to_table": "purchases",
                "to_columns": ["market_date"],
            },
        ]
    }
    validation = {
        "relationships": [
            {**relationships["relationships"][0], "status": "valid"},
            {**relationships["relationships"][1], "status": "review"},
        ]
    }
    return metadata, relationships, validation


def test_graph_preserves_nodes_edges_and_validation_status() -> None:
    metadata, relationships, validation = _artifacts()

    graph = build_knowledge_graph(metadata, relationships, validation)

    assert graph["stats"] == {"nodes": 8, "edges": 9, "tables": 3}
    statuses = {
        tuple(edge["properties"]["to_columns"]): edge["properties"]["status"]
        for edge in graph["edges"]
        if edge["type"] == "related_to"
    }
    assert statuses[("vendor_id",)] == "valid"
    assert statuses[("market_date",)] == "review"


def test_retriever_expands_from_matched_table_to_connected_tables(tmp_path: Path) -> None:
    metadata, relationships, validation = _artifacts()
    graph_path = tmp_path / "knowledge_graph.json"
    write_knowledge_graph(build_knowledge_graph(metadata, relationships, validation), graph_path)

    result = KnowledgeGraphRetriever(graph_path, metadata).retrieve("vendor sales", limit=1)

    assert {table["name"] for table in result["tables"]} == {"vendor", "purchases"}
    assert result["graph_context"]["matched_tables"] == ["vendor"]
    assert result["graph_context"]["expanded_tables"] == ["purchases"]
    assert result["relationships"][0]["status"] == "valid"
