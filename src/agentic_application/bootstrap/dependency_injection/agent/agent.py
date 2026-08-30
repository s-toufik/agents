from agentic_application.bootstrap.dependency_injection.base.base import BaseDI
import asyncio
from collections import defaultdict
from functools import cached_property
from typing import cast, Any

import aiosqlite
from httpx import AsyncClient
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from agentic.adapter.outbound.agent.graph.build_agent import build_agent
from agentic.adapter.outbound.agent.llm.factory import LLMChat
from agentic.adapter.outbound.agent.llm.mapper import ModelSettingsMapper
from agentic.adapter.outbound.agent.llm.schema import ModelConnector, ModelParameters
from agentic.adapter.outbound.agent.tool.code.python_tool_capability import PythonToolCapability
from agentic.adapter.outbound.agent.tool.specification import user_sqlite_repository, python_sandbox
from agentic.adapter.outbound.agent.tool.sql.sql_tool_capability import SQLToolCapability
from agentic.adapter.outbound.agent.tool.tool_capabilities import ToolCapability
from agentic.adapter.outbound.agent.tool.tool_registery import ToolRegistry
from agentic.application.use_case.stream_agent_usecase import on_token
from agentic_core.infrastructure.application_configuration.enum.connector_type import ConnectorType
from agentic_core.infrastructure.application_configuration.model.connector import (
    ApiConnector,
    DatabaseConnector,
)
from agentic_core.infrastructure.application_configuration.model.operation import ApiOperation
from agentic_core.infrastructure.http.adapter.httpx.factory import HttpxClientFactory
from agentic_core.infrastructure.http.configuration.http_client_configuration import (
    HttpClientSettings,
)
from agentic_core.infrastructure.http.port.async_http_client import AsyncHttpFactory
from agentic_core.infrastructure.repository.repository import RepositoryFactory, AsyncSQLRepository
from agentic_core.infrastructure.repository.sql.factory import SQLHandlerFactory
from agentic_core.infrastructure.repository.sqlite.factory import SQLiteRepositoryFactory
from agentic_core.infrastructure.repository.sqlite.mapper import SqliteSettingsMapper
from agentic_core.infrastructure.runtime.python.factory import SafeCodeFactory
from agentic_core.infrastructure.runtime.python.schema import SafeCodeSettings


class AgentDI(BaseDI):
    @cached_property
    def _llm_httpx_factory(self) -> AsyncHttpFactory:
        connector: ApiConnector = cast(
            ApiConnector, self._configuration.connector.get(ConnectorType.api).get("llm")
        )
        settings = HttpClientSettings()
        settings.client_params.base_url = connector.base_url
        settings.security.certificate = connector.certificate
        return self._register_client(
            HttpxClientFactory(http_client_settings=settings, logger=self._logging)
        )

    @property
    def _llm_http_client(self) -> AsyncClient:
        return self._llm_httpx_factory.resilient_client_instance

    async def _sqlite_connection(self, repository_name) -> aiosqlite.Connection:
        connector: DatabaseConnector = cast(
            DatabaseConnector,
            self._configuration.connector.get(ConnectorType.database).get(
                repository_name
            ),
        )
        settings = SqliteSettingsMapper(connector)()
        factory: RepositoryFactory = SQLiteRepositoryFactory(settings)
        return await factory.connection()

    async def _sqlite_repository(self, repository_name: str) -> AsyncSQLRepository:
        connector: DatabaseConnector = cast(
            DatabaseConnector,
            self._configuration.connector.get(ConnectorType.database).get(
                repository_name
            ),
        )
        settings = SqliteSettingsMapper(connector)()
        factory: RepositoryFactory = SQLiteRepositoryFactory(settings)
        self._register_repository(factory)
        return await factory.connect()

    async def _tool_registry(self) -> ToolRegistry:
        sql_handler = SQLHandlerFactory()
        sql_repository: AsyncSQLRepository = await self._sqlite_repository(repository_name="users")
        user_sqlite_too: ToolCapability = SQLToolCapability(
            repository=sql_repository,
            sql_handler=sql_handler,
            dialect=user_sqlite_repository.dialect,
            name=user_sqlite_repository.name,
            description=user_sqlite_repository.description,
            args_schema=user_sqlite_repository.args_schema,
        )

        settings: SafeCodeSettings = SafeCodeSettings(
            code_timeout=python_sandbox.timeout,
            max_memory_mb=python_sandbox.max_memory_mb,
        )
        code_semaphore: asyncio.Semaphore = asyncio.Semaphore(python_sandbox.max_concurrency)
        code_runner: ToolCapability = PythonToolCapability(
            code_factory=SafeCodeFactory(settings=settings),
            name=python_sandbox.name,
            description=python_sandbox.description,
            args_schema=python_sandbox.args_schema,
            semaphore=code_semaphore,
        )

        return ToolRegistry(tools=[user_sqlite_too, code_runner])

    def _llm_for_model(self, model_name: str, streaming: bool) -> ChatOpenAI:
        operation: ApiOperation = cast(
            ApiOperation, self._configuration.operation.get(model_name)
        )
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
                model_name=model_name,
                checkpointer=shared_checkpointer,
                tool_registry=tool_registry
            )
            graphs[key] = graph

        return graphs, shared_checkpointer
