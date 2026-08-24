import contextvars
import traceback
from typing import Optional

from agentic.application.port.outbound.agent_port import AgentPort
from agentic.application.port.outbound.sse_queue_port import SSEQueuePort
from agentic.domain.model.agent_message import AgentMessage
from agentic.domain.model.agent_request import AgentRequest
from agentic_core.infrastructure.logger.port.logger import Logger

_current_events: contextvars.ContextVar[Optional[SSEQueuePort]] = contextvars.ContextVar(
    "current_events", default=None
)


async def on_token(value: str) -> None:
    events = _current_events.get()
    if events is not None:
        await events.token(value)


class StreamAgentUseCase:
    def __init__(self, agent: AgentPort, logger: Logger) -> None:
        self._agent = agent
        self._logger = logger

    async def execute(self, request: AgentRequest, events: SSEQueuePort) -> None:
        context_events: contextvars.Token = _current_events.set(events)
        try:
            agent_message: AgentMessage = await self._agent.run(request)
            await events.final(agent_message.content, metadata=agent_message.metadata)
        except Exception as exception:
            traceback.print_exc()
            traceback_str: str = "".join(traceback.format_exception(exception))
            await events.error(traceback_str)
        finally:
            _current_events.reset(context_events)
            await events.complete()
