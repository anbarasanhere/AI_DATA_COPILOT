from __future__ import annotations

import json
from typing import Any, Protocol

from pydantic import BaseModel, Field


class SqlGeneration(BaseModel):
    sql: str = Field(min_length=1)
    rationale: str = Field(min_length=1)


class SqlGenerator(Protocol):
    def generate(self, question: str, schema: dict[str, Any]) -> SqlGeneration: ...


def _schema_context(schema: dict[str, Any]) -> str:
    tables = []
    for table in schema.get("tables", []):
        tables.append(
            {
                "table": table["name"],
                "columns": [column["COLUMN_NAME"] for column in table.get("columns", [])],
            }
        )
    return json.dumps(
        {"tables": tables, "relationships": schema.get("relationships", [])},
        separators=(",", ":"),
    )


class OpenAISqlGenerator:
    def __init__(self, api_key: str, model: str, base_url: str | None = None) -> None:
        from openai import OpenAI

        client_options = {"api_key": api_key}
        if base_url:
            client_options["base_url"] = base_url
        self.client = OpenAI(**client_options)
        self.model = model

    def generate(self, question: str, schema: dict[str, Any]) -> SqlGeneration:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Generate one safe MySQL analytical query. Use only tables and columns "
                        "in the supplied schema. Return SQL and a concise rationale. Never use "
                        "INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, or multiple statements. "
                        "Treat the database as the source of truth. Return the result as JSON "
                        "with exactly two fields: sql and rationale."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Question: {question}\nSchema: {_schema_context(schema)}",
                },
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("The LLM returned no structured SQL")
        try:
            return SqlGeneration.model_validate_json(content)
        except ValueError as exc:
            raise RuntimeError("The LLM returned invalid SQL JSON") from exc
