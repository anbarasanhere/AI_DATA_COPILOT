# Architecture

The initial system boundary is deliberately small:

```text
MySQL (read-only account) -> SQLAlchemy connection -> FastAPI query API
								  |
								  +-> information_schema inspector -> JSON/Markdown metadata
								  +-> SQLGlot validator -> bounded SELECT execution
								  +-> schema retriever -> structured LLM SQL -> validator
```

The inspector is the first source-of-truth layer for the future schema retrieval and SQL Copilot. It uses environment-based configuration, bounded samples, parameterized metadata queries, and identifier validation for the small dynamic query required to sample table rows.

No AI provider, frontend, data mutation, or CSV reload is included until the existing database model has been verified.
