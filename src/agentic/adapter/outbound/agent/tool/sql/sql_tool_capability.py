from typing import Any

from pydantic import BaseModel

from agentic.adapter.outbound.agent.tool.schema.sql_tool_input import SQLToolInput
from agentic.adapter.outbound.agent.tool.schema.tool_result import ToolResult
from agentic_core.infrastructure.repository.repository import AsyncSQLRepository
from agentic_core.infrastructure.repository.sql_handler import (
    SQLFactory,
    SQLHandler,
)


class SQLToolCapability:
    def __init__(
        self,
        repository: AsyncSQLRepository,
        sql_handler: SQLFactory,
        name: str,
        dialect: str,
        description: str,
        args_schema: type[BaseModel],
    ) -> None:
        self._repository = repository
        self._sql_handler = sql_handler
        self._dialect = dialect
        self._name = name
        self._description = description
        self._args_schema = args_schema

    @property
    def name(self) -> str:
        return self._name

    @property
    def args_schema(self) -> type[BaseModel]:
        return self._args_schema

    def schema(self) -> dict[str, Any]:
        return {
            "name": self._name,
            "description": self._description,
            "parameters": self._args_schema.model_json_schema(),
        }

    async def execute(self, request: SQLToolInput) -> ToolResult:

        call_id: str = request.call_id
        query: str = request.query
        dialect: str = request.dialect or self._dialect

        if not query.strip():
            return ToolResult(
                tool_name=self._name, id=call_id, output="", error="No SQL query provided."
            )

        try:
            sql_handler: SQLHandler = self._sql_handler(query, dialect=dialect)
            statements: str = sql_handler.transpile()
        except Exception as exception:
            return ToolResult(
                tool_name=self._name,
                id=call_id,
                output="",
                error=f"SQL validation error ({dialect}): {exception}",
            )

        try:
            result: list[dict[str, Any]] = await self._repository.execute(statements)
            return ToolResult(tool_name=self._name, id=call_id, output=str(result))
        except Exception as exc:
            return ToolResult(
                tool_name=self._name, id=call_id, output="", error=f"SQL execution error: {exc}"
            )
