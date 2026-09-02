from collections import defaultdict
from functools import cached_property
from typing import Any

import aiosqlite
from httpx import AsyncClient
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from pycraftcore.application_configuration.model.connector import ApiConnector, DatabaseConnector
from pycraftcore.application_configuration.model.operation import ApiOperation
from pycraftcore.circuit_breaker.configuration import CircuitBreakerSettings
from pycraftcore.http.configuration import HttpClientSettings, LimitsSettings
from pycraftcore.http.policy.http_error_policy import is_business_error, is_retryable
from pycraftcore.repository.adapter import SqliteSettingsMapper, SQLiteRepositoryFactory
from pycraftcore.repository.port import AsyncRepositoryFactory
from pycraftcore.resilient_http.adapter import ResilientTransportFactory
from pycraftcore.resilient_http.configuration import ResilientHttpSettings
from pycraftcore.retry.configuration import RetrySettings

from agentic.adapter.outbound.agent.graph.build_agent import build_agent
from agentic.adapter.outbound.agent.llm.factory import LLMChat
from agentic.adapter.outbound.agent.llm.mapper import ModelSettingsMapper
from agentic.adapter.outbound.agent.llm.schema import ModelConnector, ModelParameters
from agentic.adapter.outbound.agent_tool.tool_registery import ToolRegistry
from agentic.application.use_case.stream_agent_usecase import on_token
from agentic_application.bootstrap.dependency_injection.mcp.mcp import McpDI


class AgentDI(McpDI):
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

    async def _sqlite_connection(self, repository_name) -> aiosqlite.Connection:
        connector: DatabaseConnector = self._configuration.connector.database(repository_name)
        settings = SqliteSettingsMapper(connector)()
        factory: AsyncRepositoryFactory = SQLiteRepositoryFactory(settings)
        return await factory.connection()

    def _model_parameters(self, model_name: str) -> tuple[ModelConnector, ModelParameters]:
        operation: ApiOperation = self._configuration.operation.api(model_name)
        connector: ModelConnector
        parameters: ModelParameters
        connector, parameters = ModelSettingsMapper(operation)()
        return connector, parameters

    def _llm_for_model(self, model_name: str, use_streaming: bool | None = None) -> ChatOpenAI:
        connector: ModelConnector
        parameters: ModelParameters
        connector, parameters = self._model_parameters(model_name)
        if use_streaming is not None:
            parameters.use_streaming = use_streaming
        return LLMChat(connector, parameters, self._llm_http_client).create_chat_client()

    async def _build_graph(
        self,
        model_name: str,
        checkpointer: Any,
        tool_registry: ToolRegistry,
    ) -> tuple[Any, Any]:
        parameters: ModelParameters
        _, parameters = self._model_parameters(model_name)

        planner_llm: ChatOpenAI = self._llm_for_model(model_name=model_name)
        reflection_llm: ChatOpenAI = self._llm_for_model(model_name=model_name, use_streaming=False)

        graph, _ = build_agent(
            planner_llm,
            reflection_llm,
            tool_registry=tool_registry,
            checkpointer=checkpointer,
            model_parameters=parameters,
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
