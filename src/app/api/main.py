from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.agents.sql_agent import OpenAISqlGenerator, SqlGenerator
from app.db.config import get_settings
from app.db.connection import check_connection, create_mysql_engine, read_only_connection
from app.knowledge_graph.graph import build_knowledge_graph, write_knowledge_graph
from app.knowledge_graph.retriever import KnowledgeGraphRetriever
from app.sql.schema_retriever import SchemaRetriever
from app.sql.validator import validate_read_only_sql


class SchemaSearchRequest(BaseModel):  # This is a Pydantic model used to validate incoming data.
    question: str = Field(min_length=1, max_length=1000)
    limit: int = Field(default=5, ge=1, le=20)


class QueryRequest(BaseModel):
    sql: str = Field(min_length=1, max_length=100_000)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    schema_limit: int = Field(default=5, ge=1, le=20)


class QueryResponse(BaseModel):
    sql: str
    columns: list[str]
    rows: list[dict[str, Any]]
    truncated: bool


class ChatResponse(QueryResponse):
    question: str
    rationale: str
    tables: list[str]


def _json_value(
    value: object,
) -> object:  # object basically means this func, recieves any python value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, bytes):
        return value.hex()
    return value


def create_app() -> FastAPI:  # the func, is expected to return FastAPI object
    # create_app builds and configures FastAPI Application
    # It sets up the database, schema retriever, AI SQL generator, API endpoints, and finally returns the FastAPI app.
    # You can think of the function as a factory that builds your API.
    settings = get_settings()
    engine = create_mysql_engine(settings)
    metadata_path = Path(settings.mysql_output_dir) / "database_metadata.json"
    relationship_path = Path("metadata/relationships.json")
    validation_path = Path(settings.mysql_output_dir) / "relationship_validation.json"
    graph_path = Path(settings.mysql_output_dir) / "knowledge_graph.json"
    retriever = (
        SchemaRetriever(metadata_path, relationship_path) if metadata_path.exists() else None
    )
    graph_retriever = None
    if metadata_path.exists() and relationship_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        relationships = json.loads(relationship_path.read_text(encoding="utf-8"))
        validation = (
            json.loads(validation_path.read_text(encoding="utf-8"))
            if validation_path.exists()
            else None
        )
        if not graph_path.exists():
            write_knowledge_graph(
                build_knowledge_graph(metadata, relationships, validation), graph_path
            )
        graph_retriever = KnowledgeGraphRetriever(graph_path, metadata)
    generator: SqlGenerator | None = None
    if settings.llm_provider.casefold() in {"openai", "openrouter"} and settings.llm_api_key:
        generator = OpenAISqlGenerator(
            settings.llm_api_key, settings.llm_model, settings.llm_base_url
        )
    app = FastAPI(title="AI Data Copilot API", version="0.1.0")
    frontend_dir = Path(__file__).resolve().parents[3] / "frontend"
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/", include_in_schema=False)
    def frontend() -> FileResponse:
        return FileResponse(frontend_dir / "index.html")

    def execute_sql(sql: str) -> QueryResponse:
        validation = validate_read_only_sql(sql)
        if not validation.valid or validation.normalized_sql is None:
            raise HTTPException(status_code=400, detail=validation.error)
        try:
            with read_only_connection(engine) as connection:
                connection.execute(
                    text("SET SESSION MAX_EXECUTION_TIME = :timeout_ms"),
                    {"timeout_ms": settings.mysql_query_timeout_seconds * 1000},
                )
                result = connection.execute(text(validation.normalized_sql))
                rows = result.mappings().fetchmany(settings.mysql_max_result_rows)
        except SQLAlchemyError as exc:
            raise HTTPException(status_code=400, detail="Query could not be executed") from exc
        return QueryResponse(
            sql=validation.normalized_sql,
            columns=list(result.keys()),
            rows=[{key: _json_value(value) for key, value in row.items()} for row in rows],
            truncated=len(rows) == settings.mysql_max_result_rows,
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        try:
            database, version = check_connection(engine)
        except SQLAlchemyError as exc:
            raise HTTPException(status_code=503, detail="Database is unavailable") from exc
        return {"status": "ok", "database": database, "mysql_version": version}

    @app.post("/api/v1/schema/search")
    def schema_search(request: SchemaSearchRequest) -> dict[str, Any]:
        if graph_retriever is not None:
            return graph_retriever.retrieve(request.question, request.limit)
        if graph_retriever is None and retriever is None:
            raise HTTPException(status_code=503, detail="Schema metadata is unavailable")
        return retriever.retrieve(request.question, request.limit)

    @app.post("/api/v1/knowledge/search")
    def knowledge_search(request: SchemaSearchRequest) -> dict[str, Any]:
        if graph_retriever is None:
            raise HTTPException(status_code=503, detail="Knowledge graph is unavailable")
        return graph_retriever.retrieve(request.question, request.limit)

    @app.post("/api/v1/query", response_model=QueryResponse)
    def query(request: QueryRequest) -> QueryResponse:
        return execute_sql(request.sql)

    @app.post("/api/v1/chat", response_model=ChatResponse)
    def chat(request: ChatRequest) -> ChatResponse:
        if retriever is None:
            raise HTTPException(status_code=503, detail="Schema metadata is unavailable")
        if generator is None:
            raise HTTPException(status_code=503, detail="SQL generation provider is not configured")
        schema = (
            graph_retriever.retrieve(request.question, request.schema_limit)
            if graph_retriever is not None
            else retriever.retrieve(request.question, request.schema_limit)
        )
        try:
            generation = generator.generate(request.question, schema)
        except Exception as exc:
            raise HTTPException(status_code=502, detail="SQL generation failed") from exc
        result = execute_sql(generation.sql)
        return ChatResponse(
            question=request.question,
            rationale=generation.rationale,
            tables=[table["name"] for table in schema["tables"]],
            **result.model_dump(),
        )

    return app


app = create_app()
