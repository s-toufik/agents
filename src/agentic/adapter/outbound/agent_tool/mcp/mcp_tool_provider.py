from agentic.adapter.outbound.agent_tool.mcp.mcp_session_factory import McpSessionFactory
from agentic.adapter.outbound.agent_tool.mcp.mcp_tool_capability import McpToolCapability
from agentic.adapter.outbound.agent_tool.mcp.mcp_tool_input_factory import build_tool_input
from agentic.adapter.outbound.agent_tool.tool_capabilities import ToolCapability


class McpToolProvider:
    def __init__(self, client_factory: McpSessionFactory) -> None:
        self._client_factory = client_factory

    async def tools(self) -> list[ToolCapability]:
        session = self._client_factory.create_client()
        response = await session.list_tools()

        return [
            McpToolCapability(
                session=session,
                name=tool.name,
                description=tool.description or "",
                args_schema=build_tool_input(tool.name, tool.input_schema),
            )
            for tool in response.tools
        ]
