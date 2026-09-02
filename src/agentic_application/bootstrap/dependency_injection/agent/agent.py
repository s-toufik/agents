from pycraftcore.application_configuration.model.connector import (
    ApiConnector,
    DatabaseConnector,
    McpConnector,
)
from pycraftcore.application_configuration.model.operation import ApiOperation
from pycraftcore.circuit_breaker.configuration import CircuitBreakerSettings
from pycraftcore.http.configuration import HttpClientSettings, LimitsSettings
from pycraftcore.http.policy.http_error_policy import is_retryable, is_business_error
from pycraftcore.query_language.adapter import SqlHandlerFactory
from pycraftcore.repository.adapter import SqliteSettingsMapper, SQLiteRepositoryFactory
from pycraftcore.repository.port import AsyncRepositoryFactory, AsyncRepository

from pycraftcore.resilient_http.adapter import ResilientTransportFactory
from pycraftcore.resilient_http.configuration import ResilientHttpSettings
from pycraftcore.retry.configuration import RetrySettings
from pycraftcore.runtime.adapter import PythonSafeCodeFactory
from pycraftcore.runtime.configuration import SafeCodeSettings

from agentic_application.bootstrap.dependency_injection.base.base import BaseDI
import asyncio
from collections import defaultdict
from functools import cached_property
from typing import Any

import aiosqlite
from httpx import AsyncClient
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from agentic.adapter.outbound.agent.graph.build_agent import build_agent
from agentic.adapter.outbound.agent.llm.factory import LLMChat
from agentic.adapter.outbound.agent.llm.mapper import ModelSettingsMapper
from agentic.adapter.outbound.agent.llm.schema import ModelConnector, ModelParameters
from mcp.server.mcpserver import MCPServer

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
from agentic.adapter.outbound.agent_tool.specification import user_sqlite_repository, python_sandbox
from agentic.adapter.outbound.agent_tool.sql.sql_tool_capability import SQLToolCapability
from agentic.adapter.outbound.agent_tool.tool_capabilities import ToolCapability
from agentic.adapter.outbound.agent_tool.tool_registery import ToolRegistry
from agentic.application.use_case.stream_agent_usecase import on_token


class AgentDI(BaseDI):
    @cached_property
    def _llm_httpx_factory(self) -> ResilientTransportFactory:
        connector: ApiConnector = self._configuration.connector.api("llm")
        http_settings = HttpClientSettings(limits=LimitsSettings(timeout=5))
        http_settings.client_params.base_url = connector.base_url
        http_settings.security.certificate = connector.certificate

        resilient_http_settings: ResilientHttpSettings = ResilientHttpSettings(
            http=http_settings,
            retry=RetrySettings(
                retry_count=3,
                retry_delay=1,
                max_retry_delay=20,
                jitter=1,
                should_retry=is_retryable,
            ),
            circuit_breaker=CircuitBreakerSettings(
                failure_threshold=2,
                recovery_timeout=30,
                is_excluded=is_business_error,
                name="llm-gateway",
            ),
        )

        tracer = self._telemetry_provider.tracer("llm-gateway")

        return ResilientTransportFactory(
            settings=resilient_http_settings,
            trace_manager=tracer,
            logger=self._logging,
        )

    @cached_property
    def _llm_http_client(self) -> AsyncClient:
        return self._llm_httpx_factory.create_async_client()

    async def _close_llm_http_client(self) -> None:
        client = self.__dict__.pop("_llm_http_client", None)
        if client is not None:
            await client.aclose()

    @cached_property
    def _mcp_client_factory(self) -> McpClientFactory:
        # For external MCP server
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
        register_tools(self._mcp_server, await self._sql_tool_capability(), self._python_tool_capability())

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

    async def _sqlite_connection(self, repository_name) -> aiosqlite.Connection:
        connector: DatabaseConnector = self._configuration.connector.database(repository_name)
        settings = SqliteSettingsMapper(connector)()
        factory: AsyncRepositoryFactory = SQLiteRepositoryFactory(settings)
        return await factory.connection()

    async def _sqlite_repository(self, repository_name: str) -> AsyncRepository:
        connector: DatabaseConnector = self._configuration.connector.database(repository_name)
        settings = SqliteSettingsMapper(connector)()
        factory: AsyncRepositoryFactory = SQLiteRepositoryFactory(settings)
        self._register_repository(factory)
        return await factory.connect()

    async def _tool_registry(self) -> ToolRegistry:
        # The graph consumes tools exclusively through MCP -- today that's this
        # in-process, self-hosted server (SQL query, Python sandbox); a genuinely
        # external MCP server, via _mcp_client_factory, would merge in the same way.
        await self._mcp_in_process_client_factory.start()
        mcp_tools: list[ToolCapability] = await McpToolProvider(
            self._mcp_in_process_client_factory
        ).tools()

        return ToolRegistry(tools=mcp_tools)

    def _llm_for_model(self, model_name: str, streaming: bool) -> ChatOpenAI:
        operation: ApiOperation = self._configuration.operation.api(model_name)
        connector: ModelConnector
        parameters: ModelParameters
        connector, parameters = ModelSettingsMapper(operation)()
        return LLMChat(connector, parameters, self._llm_http_client).create_chat_client(
            streaming=streaming
        )

    async def _build_graph(
        self,
        model_name: str,
        checkpointer: Any,
        tool_registry: ToolRegistry,
    ) -> tuple[Any, Any]:
        planner_llm: ChatOpenAI = self._llm_for_model(model_name=model_name, streaming=True)
        reflection_llm: ChatOpenAI = self._llm_for_model(model_name=model_name, streaming=False)

        graph, _ = build_agent(
            planner_llm,
            reflection_llm,
            tool_registry=tool_registry,
            checkpointer=checkpointer,
            use_streaming=True,
            on_token=on_token,
        )

        return graph, checkpointer

    async def _build_graphs(self) -> tuple[dict[str, Any], Any]:
        model_names: dict[str, str] = {
            "gpt-oss-20b": "gpt_oss_20b",
            "mistralai/ministral-3-14b-reasoning": "ministral_3_14b_reasoning",
            "mistralai/ministral-3-3b": "ministral_3_3b",
            "qwen/qwen3-1.7b": "qwen_3_1p7b",
        }
        graphs: dict[str, Any] = defaultdict()
        connection = await self._sqlite_connection("checkpointer")
        shared_checkpointer = AsyncSqliteSaver(connection)
        tool_registry: ToolRegistry = await self._tool_registry()

        for key, model_name in model_names.items():
            graph, _ = await self._build_graph(
                model_name=model_name, checkpointer=shared_checkpointer, tool_registry=tool_registry
            )
            graphs[key] = graph

        return graphs, shared_checkpointer
