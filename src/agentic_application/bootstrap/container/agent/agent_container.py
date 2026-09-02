import os
import dotenv
from contextlib import asynccontextmanager
from functools import cached_property
from collections.abc import AsyncIterator, Callable

from fastapi import APIRouter
from mcp.server.transport_security import TransportSecuritySettings
from pycraftcore.application_configuration import ApplicationConfiguration
from pycraftcore.logger.port import Logger
from starlette.applications import Starlette

from agentic.adapter.inbound.web.controller.stream_agent_controller import StreamAgentController
from agentic.adapter.outbound.agent.lang_agent import LangAgent
from agentic.adapter.outbound.agent.streaming.sse_queue import SSEQueue
from agentic.application.port.inbound.stream_agent_port import StreamAgentPort
from agentic.application.port.outbound.agent_port import AgentPort
from agentic.application.port.outbound.sse_queue_port import SSEQueuePort
from agentic.application.use_case.stream_agent_usecase import StreamAgentUseCase
from agentic_application.bootstrap.dependency_injection.agent.agent import AgentDI
from agentic_application.bootstrap.router.agent.stream_agent_router import StreamAgentRouter


class AgentContainer(AgentDI):
    @property
    def logging(self) -> Logger:
        return self._logging

    @property
    def application_configuration(self) -> ApplicationConfiguration:
        return self._configuration

    @cached_property
    def mcp_asgi_app(self) -> Starlette:
        dotenv.load_dotenv()
        return self._mcp_server.streamable_http_app(
            streamable_http_path="/",
            transport_security=TransportSecuritySettings(allowed_hosts=[os.getenv("APP_CONNECTOR_TOOLS_MCP", "")]),
        )

    @asynccontextmanager
    async def mcp_lifespan(self) -> AsyncIterator[None]:
        _ = self.mcp_asgi_app
        async with self._mcp_server.session_manager.run():
            yield

    @property
    async def boot(self) -> tuple[bool, Exception | None]:
        try:
            # Call the factories to instance them
            _ = (self._llm_httpx_factory,)

            await self._switch_factories(mode="on")
            await self._register_mcp_tools()
            return True, None
        except Exception as exception:
            return False, exception

    async def start(self) -> None:
        await self._switch_factories(mode="on")

    async def stop(self) -> None:
        await self._switch_factories(mode="off")
        await self._close_llm_http_client()
        await self._shutdown_telemetry()
        await self._close_mcp_client_factory()
        await self._close_mcp_in_process_client_factory()

    @property
    async def create_routers(self) -> list[APIRouter]:
        return [await self._create_stream_agent_router]

    # -------------------------------------------------------------------------
    # Routers
    # -------------------------------------------------------------------------
    @cached_property
    async def _create_stream_agent_router(self) -> APIRouter:
        graphs, checkpointer = await self._build_graphs()
        agent: AgentPort = LangAgent(graphs)
        use_case: StreamAgentPort = StreamAgentUseCase(agent, self._logging)
        sse_queue: Callable[[], SSEQueuePort] = SSEQueue
        controller = StreamAgentController(use_case, sse_queue, self._logging)
        return StreamAgentRouter(controller).router
