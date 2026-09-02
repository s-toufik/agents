import asyncio
from functools import cached_property

from mcp.server.mcpserver import MCPServer
from pycraftcore.application_configuration.model.connector import DatabaseConnector, McpConnector
from pycraftcore.query_language.adapter import SqlHandlerFactory
from pycraftcore.repository.adapter import SqliteSettingsMapper, SQLiteRepositoryFactory
from pycraftcore.repository.port import AsyncRepository, AsyncRepositoryFactory
from pycraftcore.runtime.adapter import PythonSafeCodeFactory
from pycraftcore.runtime.configuration import SafeCodeSettings

from agentic.adapter.outbound.agent_tool.code.python_tool_capability import PythonToolCapability
from agentic.adapter.outbound.agent_tool.mcp.mcp_client_factory import McpClientFactory
from agentic.adapter.outbound.agent_tool.mcp.mcp_in_process_client_factory import (
    McpInProcessClientFactory,
)
from agentic.adapter.outbound.agent_tool.mcp.mcp_tool_provider import McpToolProvider
from agentic.adapter.outbound.agent_tool.mcp.server.mcp_tool_server_factory import (
    build_mcp_server,
    register_tools,
)
from agentic.adapter.outbound.agent_tool.specification import python_sandbox, user_sqlite_repository
from agentic.adapter.outbound.agent_tool.sql.sql_tool_capability import SQLToolCapability
from agentic.adapter.outbound.agent_tool.tool_capabilities import ToolCapability
from agentic.adapter.outbound.agent_tool.tool_registery import ToolRegistry
from agentic_application.bootstrap.dependency_injection.base.base import BaseDI


class McpDI(BaseDI):
    @cached_property
    def _mcp_client_factory(self) -> McpClientFactory:
        connector: McpConnector = self._configuration.connector.mcp("tools")
        return McpClientFactory(connector)

    async def _close_mcp_client_factory(self) -> None:
        factory = self.__dict__.pop("_mcp_client_factory", None)
        if factory is not None:
            await factory.close()

    @cached_property
    def _mcp_server(self) -> MCPServer:
        return build_mcp_server("agentic")

    async def _register_mcp_tools(self) -> None:
        register_tools(
            self._mcp_server, await self._sql_tool_capability(), self._python_tool_capability()
        )

    async def _sql_tool_capability(self) -> SQLToolCapability:
        sql_repository: AsyncRepository = await self._sqlite_repository(repository_name="users")
        return SQLToolCapability(
            repository=sql_repository,
            sql_handler=SqlHandlerFactory(),
            dialect=user_sqlite_repository.dialect,
            name=user_sqlite_repository.name,
            description=user_sqlite_repository.description,
            args_schema=user_sqlite_repository.args_schema,
        )

    def _python_tool_capability(self) -> PythonToolCapability:
        settings = SafeCodeSettings(
            code_timeout=python_sandbox.timeout,
            max_memory_mb=python_sandbox.max_memory_mb,
        )
        return PythonToolCapability(
            code_factory=PythonSafeCodeFactory(settings=settings),
            name=python_sandbox.name,
            description=python_sandbox.description,
            args_schema=python_sandbox.args_schema,
            semaphore=asyncio.Semaphore(python_sandbox.max_concurrency),
        )

    @cached_property
    def _mcp_in_process_client_factory(self) -> McpInProcessClientFactory:
        return McpInProcessClientFactory(self._mcp_server)

    async def _close_mcp_in_process_client_factory(self) -> None:
        factory = self.__dict__.pop("_mcp_in_process_client_factory", None)
        if factory is not None:
            await factory.close()

    async def _sqlite_repository(self, repository_name: str) -> AsyncRepository:
        connector: DatabaseConnector = self._configuration.connector.database(repository_name)
        settings = SqliteSettingsMapper(connector)()
        factory: AsyncRepositoryFactory = SQLiteRepositoryFactory(settings)
        self._register_repository(factory)
        return await factory.connect()

    async def _tool_registry(self) -> ToolRegistry:
        await self._mcp_in_process_client_factory.start()
        mcp_tools: list[ToolCapability] = await McpToolProvider(
            self._mcp_in_process_client_factory
        ).tools()

        return ToolRegistry(tools=mcp_tools)
