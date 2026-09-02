from pydantic import Field

from agentic.adapter.outbound.agent.tool.schema.tool_input import ToolInput


class SQLToolInput(ToolInput):
    query: str = Field(..., description="SQL query to execute.")
    dialect: str = Field(..., description="sqlglot source dialect.")
