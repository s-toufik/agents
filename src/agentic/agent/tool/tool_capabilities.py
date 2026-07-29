from typing import Any, Protocol

from mypy.types import TypeVar
from pydantic import BaseModel

from agentic.agent.tool.schema.tool_result import ToolResult

T = TypeVar("T")


class ToolCapability(Protocol):
    name: str
    description: str
    args_schema: type[BaseModel]

    @classmethod
    def schema(cls) -> dict[str, Any]: ...

    async def execute(self, request: T) -> ToolResult: ...
