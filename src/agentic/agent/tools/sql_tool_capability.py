from typing import Any

import sqlglot
import sqlglot.errors
from pydantic import BaseModel

from agentic.agent.schema.sql_tool_input import SQLToolInput
from agentic.agent.schema.tool_result import ToolResult
from agentic.agent.tools.tool_capabilities import ToolCapability


class SQLToolCapability(ToolCapability):

    def __init__(self, database: Any, default_dialect: str = "oracle") -> None:
        self._db = database
        self._default_dialect = default_dialect

    @property
    def name(self) -> str:
        return "sql_executor"

    @property
    def description(self) -> str:
        return "Validate and execute SQL. Defaults to Oracle dialect."

    @property
    def args_schema(self) -> type[BaseModel]:
        return SQLToolInput

    async def execute(self, **kwargs: Any) -> ToolResult:

        call_id: str = kwargs.pop("_call_id", "")
        query:   str = kwargs.get("query", "")
        dialect: str = kwargs.get("dialect", self._default_dialect)

        if not query.strip():
            return ToolResult(id=call_id, output="", error="No SQL query provided.")

        try:
            statements = sqlglot.parse(
                query, dialect=dialect, error_level=sqlglot.ErrorLevel.RAISE
            )
        except sqlglot.errors.SqlglotError as exc:
            return ToolResult(id=call_id, output="", error=f"SQL validation error ({dialect}): {exc}")

        if not statements:
            return ToolResult(id=call_id, output="", error="Empty or unparseable query.")

        transpiled = ";\n".join(
            stmt.sql(dialect="sqlite") for stmt in statements if stmt is not None
        )

        try:
            result = await self._db.execute(transpiled)
            return ToolResult(id=call_id, output=str(result))
        except Exception as exc:
            return ToolResult(id=call_id, output="", error=f"SQL execution error: {exc}")