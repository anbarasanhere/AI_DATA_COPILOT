# AI Data Engineering Copilot

## About

AI Data Engineering Copilot is a read-only analytics foundation for exploring an existing MySQL database with natural-language questions and safe SQL. It discovers tables, columns, indexes, relationships, samples, and column profiles; validates logical relationships against live data; retrieves relevant schema context; and optionally uses an OpenAI-compatible provider to generate analytical queries. A FastAPI service exposes the workflow through a lightweight browser interface, while SQLGlot, read-only transactions, and bounded results help keep query execution controlled.

This repository currently implements the Phase 1 database-discovery foundation. It connects to an existing MySQL database using environment variables and performs read-only schema introspection. It does not create, alter, truncate, or load tables.

It also includes a file-backed schema knowledge graph built from the discovery and relationship reports. The graph improves relationship-aware retrieval before SQL generation without replacing MySQL or the read-only SQL validator.

## Project Architecture 

```text
MySQL (read-only account) -> SQLAlchemy connection -> FastAPI query API
								  |
								  +-> information_schema inspector -> JSON/Markdown metadata
								  +-> SQLGlot validator -> bounded SELECT execution
								  +-> knowledge graph -> relationship-aware retriever -> structured LLM SQL -> validator
```


<img width="1279" height="577" alt="Screenshot 2026-08-28 at 3 36 00 PM" src="https://github.com/user-attachments/assets/a8538640-0069-4020-bca9-d2cdebd80f00" />
------------------------------------------------------------------------------------------------------
<img width="1279" height="577" alt="Screenshot 2026-08-28 at 3 36 28 PM" src="https://github.com/user-attachments/assets/791ad180-bc7c-4471-ae5d-98ca8fbe3751" />
------------------------------------------------------------------------------------------------------

## Setup

Use Python 3.12 or newer, then install the package and development tools:

```bash
python -m pip install -e '.[dev]'
cp .env.example .env
```

Edit `.env` with a MySQL read-only account. Do not commit `.env` or share its password.

## Inspect MySQL

```bash
inspect-mysql --output-dir artifacts
```

The command checks the selected database, discovers tables and columns through `information_schema`, reports indexes and declared foreign keys, and writes:

- `artifacts/database_metadata.json`
- `artifacts/database_schema.md`

Samples are bounded by `MYSQL_SAMPLE_ROWS`. The command is intended to be run against the database that already contains the nine CSV-derived datasets.

## Current status

The supplied relationship diagram is recorded in `metadata/relationships.json`. The live database now contains all diagram tables, including `vendor`, plus an additional `datetime_demo` table. `vendor.vendor_id` is declared as a primary key, but the remaining diagram relationships are not declared as live foreign keys. The logical relationships are used for schema retrieval, while live constraints remain pending validation.

Validate the diagram relationships against live values with:

```bash
validate-relationships
```

The current report has 10 valid relationships and one review item: 3 `customer_purchases.customer_id` values do not match `customer.customer_id`. No foreign-key constraints are added automatically.

Build the knowledge graph after generating or updating the reports:

```bash
build-knowledge-graph
```

This writes `artifacts/knowledge_graph.json` with database, table, column, and relationship nodes. Relationship edges retain their `valid`, `review`, or `unvalidated` status and source artifact.

## Query API

Start the read-only API with:

```bash
PYTHONPATH=src uvicorn app.api.main:app --reload
```

Available endpoints:

- `GET /health` checks the MySQL connection.
- `POST /api/v1/schema/search` retrieves relevant tables for a question.
- `POST /api/v1/knowledge/search` retrieves relevant tables plus one-hop graph relationship context.
- `POST /api/v1/query` validates and executes one read-only `SELECT` or `WITH` query.
- `POST /api/v1/chat` retrieves schema, generates structured SQL, validates it, and executes it.

Natural-language SQL generation requires `LLM_PROVIDER=openai` and an OpenAI `LLM_API_KEY` in `.env`. Use a model such as `gpt-4o-mini`. Leave `LLM_BASE_URL` empty to use the default OpenAI endpoint. OpenRouter is also supported by setting `LLM_PROVIDER=openrouter`, an OpenRouter-compatible model, and `LLM_BASE_URL=https://openrouter.ai/api/v1`. Without a supported provider and API key, `/api/v1/chat` returns `503` and does not execute anything.

run the project
--
source .venv/bin/activate && python --version && pytest -q

source .venv/bin/activate && command -v uvicorn && command -v inspect-mysql && command -v validate-relationships

PYTHONPATH=src uvicorn app.api.main:app --port 8000
