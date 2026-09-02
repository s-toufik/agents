from typing import Any, Protocol, TypeVar

from agentic.adapter.outbound.agent.tool.schema.tool_input import ToolInput
from agentic.adapter.outbound.agent.tool.schema.tool_result import ToolResult

T = TypeVar("T", bound=ToolInput)


class ToolCapability(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def args_schema(self) -> type[ToolInput]: ...

    def schema(self) -> dict[str, Any]: ...

    async def execute(self, request: T) -> ToolResult: ...
