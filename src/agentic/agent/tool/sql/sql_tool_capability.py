from typing import Any

from pydantic import BaseModel

from agentic.agent.tool.schema.sql_tool_input import SQLToolInput
from agentic.agent.tool.schema.tool_result import ToolResult
from agentic.infrastructure.repository.repository import AsyncSQLRepository
from agentic.infrastructure.repository.sql_handler import (
    SQLFactory,
    DEFAULT_DIALECT,
    FORBIDDEN_STATEMENTS,
    SQLHandler,
)


class SQLToolCapability:
    name: str = "sql_executor"
    description: str = f"Execute SQL queries. Defaults to {
        DEFAULT_DIALECT
    } dialect. forbidden operations are: {
        ', '.join([item.__name__ for item in FORBIDDEN_STATEMENTS])
    } "
    args_schema: type[BaseModel] = SQLToolInput

    def __init__(
        self,
        repository: AsyncSQLRepository,
        sql_handler: SQLFactory,
        default_dialect: str = DEFAULT_DIALECT,
    ) -> None:
        self._repository = repository
        self._sql_handler = sql_handler
        self._default_dialect = default_dialect

    @classmethod
    def schema(cls) -> dict[str, Any]:
        return {
            "name": cls.name,
            "description": cls.description,
            "parameters": cls.args_schema.model_json_schema(),
        }

    async def execute(self, request: SQLToolInput) -> ToolResult:

        call_id: str = request.call_id
        query: str = request.query
        dialect: str = request.dialect or self._default_dialect

        if not query.strip():
            return ToolResult(
                tool_name=self.name, id=call_id, output="", error="No SQL query provided."
            )

        try:
            sql_handler: SQLHandler = self._sql_handler(query, dialect=dialect)
            statements: str = sql_handler.transpile()
        except Exception as exception:
            return ToolResult(
                tool_name=self.name,
                id=call_id,
                output="",
                error=f"SQL validation error ({dialect}): {exception}",
            )

        try:
            result: list[dict[str, Any]] = await self._repository.execute(statements)
            return ToolResult(tool_name=self.name, id=call_id, output=str(result))
        except Exception as exc:
            return ToolResult(
                tool_name=self.name, id=call_id, output="", error=f"SQL execution error: {exc}"
            )
