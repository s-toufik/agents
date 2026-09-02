from mcp.server.mcpserver import MCPServer

from agentic.adapter.outbound.agent_tool.code.python_tool_capability import PythonToolCapability
from agentic.adapter.outbound.agent_tool.schema.python_tool_input import PythonToolInput
from agentic.adapter.outbound.agent_tool.schema.sql_tool_input import SQLToolInput
from agentic.adapter.outbound.agent_tool.sql.sql_tool_capability import SQLToolCapability


def build_mcp_server(name: str) -> MCPServer:
    return MCPServer(name=name)


def register_tools(
    server: MCPServer, sql_tool: SQLToolCapability, python_tool: PythonToolCapability
) -> None:

    sql_schema = sql_tool.schema()

    @server.tool(name=sql_tool.name, description=sql_schema["description"])
    async def _query_users(query: str, dialect: str) -> str:
        request = SQLToolInput(query=query, dialect=dialect)
        request.call_id = "mcp"
        result = await sql_tool.execute(request)
        return result.content

    python_schema = python_tool.schema()

    @server.tool(name=python_tool.name, description=python_schema["description"])
    async def _run_python(code: str) -> str:
        request = PythonToolInput(code=code)
        request.call_id = "mcp"
        result = await python_tool.execute(request)
        return result.content
