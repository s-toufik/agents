from collections import defaultdict
from functools import cached_property
from typing import Optional, cast, Any

import aiosqlite
from fastapi import APIRouter
from httpx import AsyncClient
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from agentic.adapter.inbound.web.controller.stream_agent_controller import StreamAgentController
from agentic.adapter.outbound.agent.build_agent import build_agent
from agentic.adapter.outbound.agent.lang_agent import LangAgent
from agentic.adapter.outbound.agent.llm.factory import LLMChat
from agentic.adapter.outbound.agent.llm.mapper import ModelSettingsMapper
from agentic.adapter.outbound.agent.llm.schema import ModelConnector, ModelParameters
from agentic.adapter.outbound.agent.sse_queue import SSEQueue
from agentic.adapter.outbound.agent.tool.code.python_tool_capability import PythonToolCapability
from agentic.adapter.outbound.agent.tool.specification import user_sqlite_repository, python_sandbox
from agentic.adapter.outbound.agent.tool.sql.sql_tool_capability import SQLToolCapability
from agentic.adapter.outbound.agent.tool.tool_capabilities import ToolCapability
from agentic.adapter.outbound.agent.tool.tool_registery import ToolRegistry
from agentic.application.port.inbound.stream_agent_port import StramAgentPort
from agentic.application.port.outbound.agent_port import AgentPort
from agentic.application.use_case.stream_agent_usecase import on_token, StreamAgentUseCase
from agentic_application.bootstrap.configuration.application_configuration import (
    LoadApplicationConfiguration,
)
from agentic_application.bootstrap.configuration.application_logger import create_logger
from agentic_application.bootstrap.router.stream_agent_router import StreamAgentRouter
from agentic_core.infrastructure.application_configuration.enum.connector_type import ConnectorType
from agentic_core.infrastructure.application_configuration.model.configuration import (
    ApplicationConfiguration,
)
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
from agentic_core.infrastructure.logger.adapter.loguru_logger import LoguruLogger
from agentic_core.infrastructure.logger.port.logger import Logger
from agentic_core.infrastructure.repository.repository import RepositoryFactory, AsyncSQLRepository
from agentic_core.infrastructure.repository.sql.factory import SQLHandlerFactory
from agentic_core.infrastructure.repository.sqlite.factory import SQLiteRepositoryFactory
from agentic_core.infrastructure.repository.sqlite.mapper import SqliteSettingsMapper
from agentic_core.infrastructure.runtime.python.factory import SafeCodeFactory


class Container:
    # -------------------------------------------------------------------------
    # Core
    # -------------------------------------------------------------------------
    def __init__(self):
        self.logging = None
        self.application_configuration = None
        self._clients: list[AsyncHttpFactory] = []
        self._repositories: list[RepositoryFactory] = []

    def _register_client(self, client: AsyncHttpFactory) -> AsyncHttpFactory:
        self._clients.append(client)
        return client

    def _register_repository(self, repository: RepositoryFactory) -> RepositoryFactory:
        self._repositories.append(repository)
        return repository

    async def _switch_factories(self, mode: str) -> None:
        if mode.lower() == "on":
            for client in self._clients:
                if hasattr(client, "start"):
                    await client.start()
            for repository in self._repositories:
                if hasattr(repository, "connect"):
                    await repository.connect()
        elif mode.lower() == "off":
            for client in self._clients:
                if hasattr(client, "close"):
                    await client.close()
            for repository in self._repositories:
                if hasattr(repository, "disconnect"):
                    await repository.disconnect()
        else:
            raise ValueError(f"Invalid mode: {mode}")

    @property
    async def boot(self) -> tuple[bool, Optional[Exception]]:
        try:
            self.application_configuration = self._configuration
            self.logging = self._logging

            # Call the factories to instance them
            _ = (self._llm_httpx_factory,)

            await self._switch_factories(mode="on")
            return True, None
        except Exception as exception:
            return False, exception

    async def start(self) -> None:
        await self._switch_factories(mode="on")

    async def stop(self) -> None:
        await self._switch_factories(mode="off")

    # -------------------------------------------------------------------------
    # Routers
    # -------------------------------------------------------------------------
    @cached_property
    async def _create_stream_agent_router(self) -> APIRouter:
        graphs, checkpointer = await self._build_graphs()
        agent: AgentPort = LangAgent(graphs)
        use_case: StramAgentPort = StreamAgentUseCase(agent)
        controller = StreamAgentController(use_case, SSEQueue, self._logging)
        return StreamAgentRouter(controller).router

    @property
    async def create_routers(self) -> list[APIRouter]:
        return [await self._create_stream_agent_router]

    # -------------------------------------------------------------------------
    # Infrastructure
    # -------------------------------------------------------------------------
    @cached_property
    def _logging(self) -> Logger:
        return create_logger(logger=LoguruLogger())

    @cached_property
    def _configuration(self) -> ApplicationConfiguration:
        return LoadApplicationConfiguration(self._logging)()

    @cached_property
    def _llm_httpx_factory(self) -> AsyncHttpFactory:
        connector: ApiConnector = cast(
            ApiConnector, self.application_configuration.connector.get(ConnectorType.api).get("llm")
        )
        settings = HttpClientSettings()
        settings.client_params.base_url = connector.base_url
        settings.security.certificate = connector.certificate
        return self._register_client(
            HttpxClientFactory(http_client_settings=settings, logger=self.logging)
        )

    @property
    def _llm_http_client(self) -> AsyncClient:
        return self._llm_httpx_factory.resilient_client_instance

    async def _sqlite_connection(self, repository_name) -> aiosqlite.Connection:
        connector: DatabaseConnector = cast(
            DatabaseConnector,
            self.application_configuration.connector.get(ConnectorType.database).get(
                repository_name
            ),
        )
        settings = SqliteSettingsMapper(connector)()
        factory: RepositoryFactory = SQLiteRepositoryFactory(settings)
        return await factory.connection()

    async def _sqlite_repository(self, repository_name: str) -> AsyncSQLRepository:
        connector: DatabaseConnector = cast(
            DatabaseConnector,
            self.application_configuration.connector.get(ConnectorType.database).get(
                repository_name
            ),
        )
        settings = SqliteSettingsMapper(connector)()
        factory: RepositoryFactory = SQLiteRepositoryFactory(settings)
        self._register_repository(factory)
        return await factory.connect()

    async def _tool_registry(self) -> ToolRegistry:
        sql_handler = SQLHandlerFactory()
        user_sqlite = await self._sqlite_repository(repository_name="users")
        user_sqlite_too: ToolCapability = SQLToolCapability(
            repository=user_sqlite,
            sql_handler=sql_handler,
            dialect=user_sqlite_repository.dialect,
            name=user_sqlite_repository.name,
            description=user_sqlite_repository.description,
            args_schema=user_sqlite_repository.args_schema,
        )

        code_runner: ToolCapability = PythonToolCapability(
            code_factory=SafeCodeFactory(),
            name=python_sandbox.name,
            description=python_sandbox.description,
            args_schema=python_sandbox.args_schema,
            timeout=python_sandbox.timeout,
            max_memory_mb=python_sandbox.max_memory_mb,
        )

        return ToolRegistry(tools=[user_sqlite_too, code_runner])

    def _llm_for_model(self, model_name: str, streaming: bool) -> ChatOpenAI:
        operation: ApiOperation = cast(
            ApiOperation, self.application_configuration.operation.get(model_name)
        )
        connector: ModelConnector
        parameters: ModelParameters
        connector, parameters = ModelSettingsMapper(operation)()
        return LLMChat(connector, parameters, self._llm_http_client).create_chat_client(
            streaming=streaming
        )

    async def _build_graph(
        self, model_name: str, streaming: bool, checkpointer: Any
    ) -> tuple[Any, Any]:
        planner_llm: ChatOpenAI = self._llm_for_model(model_name=model_name, streaming=streaming)
        reflection_llm: ChatOpenAI = self._llm_for_model(model_name=model_name, streaming=streaming)
        tool_registry: ToolRegistry = await self._tool_registry()

        graph, _ = build_agent(
            planner_llm,
            reflection_llm,
            tool_registry=tool_registry,
            checkpointer=checkpointer,
            use_streaming=streaming,
            on_token=on_token,
        )

        return graph, checkpointer

    async def _build_graphs(self) -> tuple[dict[str, Any], Any]:
        model_names: dict[str, str] = {
            "gpt-oss-20b": "gpt_oss_20b",
            "mistralai/ministral-3-14b-reasoning": "ministral_3_14b_reasoning",
            "mistralai/ministral-3-3b": "ministral_3_3b",
        }
        graphs: dict[str, Any] = defaultdict()
        connection = await self._sqlite_connection("checkpointer")
        shared_checkpointer = AsyncSqliteSaver(connection)

        for key, model_name in model_names.items():
            graph, _ = await self._build_graph(
                model_name=model_name, streaming=True, checkpointer=shared_checkpointer
            )
            graphs[key] = graph

        return graphs, shared_checkpointer
