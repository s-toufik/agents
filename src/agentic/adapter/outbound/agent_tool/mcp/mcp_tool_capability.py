from typing import Any

from mcp import ClientSession
from mcp.types import TextContent

from agentic.adapter.outbound.agent_tool.schema.tool_input import ToolInput
from agentic.adapter.outbound.agent_tool.schema.tool_result import ToolResult


class McpToolCapability:
    def __init__(
        self,
        session: ClientSession,
        name: str,
        description: str,
        args_schema: type[ToolInput],
    ) -> None:
        self._session = session
        self._name = name
        self._description = description
        self._args_schema = args_schema

    @property
    def name(self) -> str:
        return self._name

    @property
    def args_schema(self) -> type[ToolInput]:
        return self._args_schema

    def schema(self) -> dict[str, Any]:
        return {
            "name": self._name,
            "description": self._description,
            "parameters": self._args_schema.model_json_schema(),
        }

    async def execute(self, request: ToolInput) -> ToolResult:
        call_id: str = request.call_id
        arguments: dict[str, Any] = request.model_dump(exclude_none=True)

        try:
            result = await self._session.call_tool(self._name, arguments)
        except Exception as exception:
            return ToolResult(
                tool_name=self._name, id=call_id, output="", error=f"MCP call error: {exception}"
            )

        output = self._stringify(result.content)
        if result.is_error:
            return ToolResult(tool_name=self._name, id=call_id, output="", error=output)
        return ToolResult(tool_name=self._name, id=call_id, output=output)

    @staticmethod
    def _stringify(content: list[Any]) -> str:
        return "\n".join(
            block.text if isinstance(block, TextContent) else str(block) for block in content
        )
