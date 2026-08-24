from functools import cached_property
from typing import Optional, Callable

from fastapi import APIRouter

from agentic.adapter.inbound.web.controller.stream_agent_controller import StreamAgentController
from agentic.adapter.outbound.agent.lang_agent import LangAgent
from agentic.adapter.outbound.agent.streaming.sse_queue import SSEQueue
from agentic.application.port.inbound.stream_agent_port import StramAgentPort
from agentic.application.port.outbound.agent_port import AgentPort
from agentic.application.port.outbound.sse_queue_port import SSEQueuePort
from agentic.application.use_case.stream_agent_usecase import StreamAgentUseCase
from agentic_application.bootstrap.dependency_injection.agent.agent import AgentDI
from agentic_application.bootstrap.router.agent.stream_agent_router import StreamAgentRouter
from agentic_core.infrastructure.application_configuration.model.configuration import ApplicationConfiguration
from agentic_core.infrastructure.logger.port.logger import Logger


class AgentContainer(AgentDI):
    @property
    def logging(self) -> Logger:
        return self._logging

    @property
    def application_configuration(self) -> ApplicationConfiguration:
        return self._configuration

    @property
    async def boot(self) -> tuple[bool, Optional[Exception]]:
        try:
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
        use_case: StramAgentPort = StreamAgentUseCase(agent, self._logging)
        sse_queue: Callable[[], SSEQueuePort] = SSEQueue
        controller = StreamAgentController(use_case, sse_queue, self._logging)
        return StreamAgentRouter(controller).router
