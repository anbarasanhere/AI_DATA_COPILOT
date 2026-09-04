from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.knowledge_graph.graph import build_knowledge_graph, write_knowledge_graph


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a schema knowledge graph from JSON artifacts."
    )
    parser.add_argument("--metadata", default="artifacts/database_metadata.json")
    parser.add_argument("--relationships", default="metadata/relationships.json")
    parser.add_argument("--validation", default="artifacts/relationship_validation.json")
    parser.add_argument("--output", default="artifacts/knowledge_graph.json")
    args = parser.parse_args()

    metadata = json.loads(Path(args.metadata).read_text(encoding="utf-8"))
    relationships = json.loads(Path(args.relationships).read_text(encoding="utf-8"))
    validation_path = Path(args.validation)
    validation = (
        json.loads(validation_path.read_text(encoding="utf-8"))
        if validation_path.exists()
        else None
    )
    graph = build_knowledge_graph(metadata, relationships, validation)
    write_knowledge_graph(graph, Path(args.output))
    print(f"Built graph with {graph['stats']['nodes']} nodes and {graph['stats']['edges']} edges")
    print(f"Graph written to {args.output}")


if __name__ == "__main__":
    main()
