# Architecture

The initial system boundary is deliberately small:

```text
MySQL (read-only account) -> SQLAlchemy connection -> FastAPI query API
								  |
								  +-> information_schema inspector -> JSON/Markdown metadata
								  +-> SQLGlot validator -> bounded SELECT execution
								  +-> knowledge graph -> relationship-aware retriever -> structured LLM SQL -> validator
```

The inspector is the first source-of-truth layer for the future schema retrieval and SQL Copilot. It uses environment-based configuration, bounded samples, parameterized metadata queries, and identifier validation for the small dynamic query required to sample table rows.

No AI provider, frontend, data mutation, or CSV reload is included until the existing database model has been verified.

## Knowledge graph layer

`src/app/knowledge_graph/graph.py` creates a deterministic JSON graph from
`artifacts/database_metadata.json`, `metadata/relationships.json`, and the optional
`artifacts/relationship_validation.json` report. Nodes represent the database,
tables, and columns. Relationship edges contain join columns, validation status,
and source provenance.

`KnowledgeGraphRetriever` matches table and column terms, then expands one
relationship hop. The API uses this context for schema search and SQL generation
while retaining the existing SQLGlot read-only validation. Run
`build-knowledge-graph` to regenerate the artifact; the API also creates it on
startup when it is missing.
