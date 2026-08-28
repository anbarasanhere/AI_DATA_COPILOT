# AI Data Copilot Implementation Guide

This document records the implementation completed so far for the AI Data Copilot project. It is intended as a practical reference for setup, architecture, code ownership, validation, and local execution.

## 1. Project Goal

The project is a Phase 1 database-discovery and read-only analytics foundation. It connects to an existing MySQL database, inspects its schema and data quality, retrieves relevant schema context for a question, validates SQL, and exposes the workflow through a FastAPI API and browser frontend.

The system does not create, alter, truncate, insert into, update, or reload database tables.

## 2. Technology Stack

- Python 3.12+
- FastAPI for the HTTP API
- Uvicorn for local development serving
- SQLAlchemy for MySQL connections and execution
- PyMySQL as the MySQL driver
- Pydantic Settings for environment configuration
- SQLGlot for MySQL SQL parsing and read-only validation
- OpenAI-compatible client for optional SQL generation through OpenAI or OpenRouter
- Plain HTML, CSS, and JavaScript for the frontend
- pytest, Ruff, and mypy as development tools

## 3. Repository Structure

```text
pyproject.toml                 Package metadata, dependencies, scripts, and tool settings
README.md                      Setup and current-status overview
implementation.md              This implementation reference

metadata/
  relationships.json           Logical relationship contract from the supplied diagram

artifacts/
  database_metadata.json        Generated database metadata and profiles
  database_schema.md            Generated human-readable schema report
  relationship_validation.json Generated relationship validation data
  relationship_validation.md   Generated relationship validation report

docs/
  architecture.md              System boundary and data-flow description
  database_schema.md            Schema documentation

frontend/
  index.html                   Application shell and controls
  app.js                       API calls and result rendering
  styles.css                   Responsive application styling

src/app/
  api/main.py                  FastAPI application, routes, and query execution
  agents/sql_agent.py          Optional structured LLM SQL generation
  db/config.py                 Environment-backed settings
  db/connection.py             MySQL engine and read-only connection helpers
  db/inspect.py                inspect-mysql CLI and report generation
  db/introspection.py          information_schema inspection implementation
  db/relationships.py          Logical relationship validation queries
  db/validate_relationships.py validate-relationships CLI
  sql/schema_retriever.py      Token-based schema and relationship retrieval
  sql/validator.py             Read-only SQL parser and validator

tests/
  test_introspection.py        Identifier and SQL validation tests
```

## 4. Environment Setup

Use Python 3.12 or newer. The repository uses a virtual environment at `.venv` in the current workspace.

Install the project and development dependencies:

```bash
python -m pip install -e '.[dev]'
```

If the shell does not expose the `python` command, use the virtual environment executable directly:

```bash
./.venv/bin/python -m pip install -e '.[dev]'
```

Create the environment file:

```bash
cp .env.example .env
```

Configure a MySQL read-only account in `.env`. Do not commit `.env` or expose its password.

### Required database settings

```dotenv
MYSQL_DATABASE=your_database
MYSQL_USER=read_only_user
MYSQL_PASSWORD=your_password
```

### Optional database settings

```dotenv
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_POOL_SIZE=2
MYSQL_POOL_TIMEOUT_SECONDS=10
MYSQL_CONNECT_TIMEOUT_SECONDS=5
MYSQL_SAMPLE_ROWS=5
MYSQL_MAX_TABLES=200
MYSQL_QUERY_TIMEOUT_SECONDS=30
MYSQL_MAX_RESULT_ROWS=1000
MYSQL_OUTPUT_DIR=artifacts
```

### Optional natural-language SQL settings

The `/api/v1/chat` endpoint is disabled unless an LLM provider and API key are configured.

```dotenv
LLM_PROVIDER=openrouter
LLM_API_KEY=your_key
LLM_MODEL=openai/gpt-4o-mini
LLM_BASE_URL=https://openrouter.ai/api/v1
```

`LLM_PROVIDER=openai` is also supported when using the default OpenAI endpoint. The provider, model, and base URL are configurable.

## 5. Database Connection Implementation

`src/app/db/config.py` defines a Pydantic `Settings` object. Settings are loaded from `.env` and environment variables, with validation for ports, pool limits, timeouts, table limits, and result limits. `get_settings()` is cached so the application uses one consistent configuration instance.

The `database_url` property builds a MySQL SQLAlchemy URL using the configured credentials.

`src/app/db/connection.py` provides three database operations:

1. `create_mysql_engine()` creates a SQLAlchemy engine with connection health checks, pool sizing, pool timeout, and MySQL connection timeout.
2. `read_only_connection()` opens a connection and executes `SET SESSION TRANSACTION READ ONLY` before yielding it.
3. `check_connection()` runs `SELECT DATABASE(), VERSION()` and returns the selected database and MySQL version.

The read-only transaction setting is applied to API queries, introspection, and relationship validation.

## 6. Schema Introspection

The `inspect-mysql` command is defined in `src/app/db/inspect.py` and implemented by `src/app/db/introspection.py`.

Run it with:

```bash
PYTHONPATH=src ./.venv/bin/inspect-mysql --output-dir artifacts
```

The command:

1. Loads database settings.
2. Creates a MySQL engine.
3. Confirms the connected database matches `MYSQL_DATABASE`.
4. Reads table metadata from `information_schema.TABLES`.
5. Reads columns from `information_schema.COLUMNS` in ordinal order.
6. Reads indexes from `information_schema.STATISTICS`.
7. Reads declared foreign keys from `information_schema.KEY_COLUMN_USAGE`.
8. Retrieves a bounded number of sample rows per table.
9. Profiles every column using total rows, null count, and distinct count.
10. Writes JSON and Markdown reports.
11. Disposes the engine in a `finally` block.

The inspection is bounded by `MYSQL_MAX_TABLES` and `MYSQL_SAMPLE_ROWS`.

Dynamic table and column names cannot be bound as normal SQL parameters, so `quote_identifier()` first validates identifiers against the allowed MySQL identifier pattern and then wraps them in backticks. This prevents SQL expressions or injected statements from being used as identifiers.

Generated files:

- `artifacts/database_metadata.json`
- `artifacts/database_schema.md`

The Markdown renderer identifies primary-key columns from the `PRIMARY` index and includes column types, nullability, null counts, distinct counts, comments, and declared foreign keys.

## 7. Logical Relationship Validation

`metadata/relationships.json` stores the relationship contract from the supplied diagram. It is metadata only and does not alter MySQL.

Run validation with:

```bash
PYTHONPATH=src ./.venv/bin/validate-relationships
```

`src/app/db/validate_relationships.py` first performs a no-sample schema inspection to build the available table and column map. `src/app/db/relationships.py` then checks each declared relationship.

For each relationship, validation checks:

- Whether the parent and child tables exist.
- Whether all parent and child columns exist.
- Child row count.
- Child rows with null relationship keys.
- Child rows whose keys do not match a parent row.
- Duplicate parent keys.

A relationship is marked `valid` when there are no orphan child rows and no duplicate parent keys. Missing tables or columns receive explicit missing statuses. Otherwise the relationship is marked `review`.

Generated files:

- `artifacts/relationship_validation.json`
- `artifacts/relationship_validation.md`

Current recorded result:

- 10 relationships are valid.
- 1 relationship requires review.
- `customer_purchases.customer_id` contains 3 values that do not match `customer.customer_id`.
- `vendor.vendor_id` is a live primary key.
- The remaining diagram relationships are logical relationships and are not currently declared as live foreign keys.
- The live database also contains `datetime_demo`, which is not shown in the supplied diagram.

## 8. Schema Retrieval

`src/app/sql/schema_retriever.py` implements a lightweight token-based retriever.

For an incoming question it:

1. Tokenizes the question into lowercase alphanumeric and underscore tokens.
2. Scores tables when tokens match or occur within a table or column name.
3. Sorts matches by score and then table name.
4. Returns up to the requested table limit.
5. Includes logical relationships touching any selected table.

The result has this shape:

```json
{
  "tables": [],
  "relationships": []
}
```

This is intentionally simple for the current phase and uses the generated metadata as its source of truth.

## 9. SQL Safety Validation

`src/app/sql/validator.py` defines `validate_read_only_sql()` and the immutable `SqlValidation` result.

Validation performs the following checks:

1. Rejects empty SQL.
2. Parses using SQLGlot with the MySQL dialect.
3. Rejects parse errors.
4. Rejects multiple SQL statements.
5. Allows only `SELECT` or `WITH` queries, represented by SQLGlot as `Select` or `Union` expressions.
6. Returns normalized MySQL SQL for execution.

Mutation statements such as `DROP`, `INSERT`, `UPDATE`, `DELETE`, `ALTER`, and `CREATE` are rejected. API execution also uses the configured maximum execution time and maximum result-row count.

## 10. Optional LLM SQL Generation

`src/app/agents/sql_agent.py` defines:

- `SqlGeneration`, a structured response containing `sql` and `rationale`.
- `SqlGenerator`, a protocol for generator implementations.
- `OpenAISqlGenerator`, an OpenAI-compatible implementation.

The generator sends the user question and a compact schema context containing selected tables, columns, and logical relationships. The system prompt instructs the model to generate one safe MySQL analytical query using only the supplied schema and to return structured JSON.

The generated SQL is not trusted directly. It is always passed through the same SQLGlot read-only validator before execution.

## 11. FastAPI API

`src/app/api/main.py` creates the FastAPI application and mounts the `frontend` directory at `/static`. The root route `/` returns `frontend/index.html`.

Start the API locally:

```bash
PYTHONPATH=src ./.venv/bin/uvicorn app.api.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

### Endpoints

#### `GET /health`

Checks the MySQL connection and returns the database name and MySQL version. Returns HTTP 503 when the database is unavailable.

#### `POST /api/v1/schema/search`

Request:

```json
{"question":"Which products generated the highest revenue?","limit":5}
```

Returns relevant tables and logical relationships. It returns HTTP 503 when generated schema metadata is unavailable.

#### `POST /api/v1/query`

Request:

```json
{"sql":"SELECT COUNT(*) AS vendor_count FROM vendor;"}
```

The SQL is validated, normalized, executed in a read-only connection, and returned with columns, rows, and a truncation flag.

#### `POST /api/v1/chat`

Request:

```json
{"question":"Which products generated the highest revenue?","schema_limit":5}
```

The endpoint retrieves schema, calls the configured LLM, validates the generated SQL, executes it, and returns the question, rationale, source tables, SQL, columns, rows, and truncation flag.

It returns HTTP 503 when metadata or the LLM provider is not configured, and HTTP 502 when generation fails.

## 12. Frontend Implementation

The frontend is a static HTML/CSS/JavaScript interface served by FastAPI.

`frontend/index.html` provides:

- Sidebar workspace navigation.
- Connection status display.
- Natural-language question textarea.
- Quick question cards.
- Results area.
- Direct read-only SQL editor.
- Ask Copilot and Run query controls.

`frontend/app.js` provides:

- `escapeHtml()` for safe rendering of server-returned values.
- `renderResult()` for tabular results, rationale, source tables, and read-only status.
- `showError()` for request errors.
- `postJson()` for JSON POST requests and HTTP error handling.
- `/api/v1/chat` submission for natural-language questions.
- `/api/v1/query` submission for direct SQL.
- Quick-card population and New analysis reset behavior.

`frontend/styles.css` supplies the responsive layout, sidebar, prompt panel, result table, SQL editor, status indicators, color variables, and mobile layout. The interface uses DM Sans and Space Grotesk and collapses the sidebar and quick-question layout on small screens.

## 13. Tests and Verification

Run the test suite:

```bash
./.venv/bin/pytest
```

The current tests cover:

- Accepting a valid MySQL identifier.
- Rejecting an unsafe SQL expression as an identifier.
- Accepting a normal `SELECT` query.
- Accepting a `WITH` query.
- Rejecting mutation SQL.
- Rejecting multiple SQL statements.

Run static checks when the development dependencies are installed:

```bash
./.venv/bin/ruff check .
./.venv/bin/mypy src
```

Smoke-test the running server:

```bash
curl -fsS http://127.0.0.1:8000/
curl -fsS http://127.0.0.1:8000/openapi.json
curl -fsS http://127.0.0.1:8000/health
```

The first two routes were verified during the current implementation session. `/health` depends on a reachable configured MySQL database.

## 14. Current Runbook

From the repository root:

```bash
source .venv/bin/activate
PYTHONPATH=src .venv/bin/inspect-mysql --output-dir artifacts
PYTHONPATH=src .venv/bin/validate-relationships
PYTHONPATH=src .venv/bin/uvicorn app.api.main:app --reload
```

Then browse to `http://127.0.0.1:8000`.

The direct SQL runner can work without an LLM provider. Natural-language analysis requires both generated metadata and valid LLM settings, in addition to a reachable MySQL database.

## 15. Deliberate Scope and Next Implementation Areas

The current foundation intentionally leaves these areas for later phases:

- Fixing or explaining the 3 orphan customer identifiers.
- Adding live foreign-key constraints after relationship review.
- More advanced schema retrieval, such as embeddings or semantic ranking.
- Broader SQL test coverage and API integration tests.
- Authentication and authorization for the API.
- Production deployment configuration.
- Query auditing, rate limiting, and richer observability.
- Additional frontend schema-explorer behavior.
- More robust database error details and user-facing loading states.

Any future SQL generation feature must preserve the existing defense-in-depth model: read-only database credentials, read-only transactions, SQL parsing, single-statement enforcement, and result limits.
