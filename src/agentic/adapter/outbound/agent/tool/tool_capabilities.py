from typing import Any, Protocol

from mypy.types import TypeVar
from pydantic import BaseModel

from agentic.adapter.outbound.agent.tool.schema.tool_result import ToolResult

T = TypeVar("T")


class ToolCapability(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def args_schema(self) -> type[BaseModel]: ...

    @classmethod
    def schema(cls) -> dict[str, Any]: ...

    async def execute(self, request: T) -> ToolResult: ...
