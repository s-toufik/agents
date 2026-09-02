import contextvars
import traceback

from pycraftcore.logger.port import Logger

from agentic.application.port.outbound.agent_port import AgentPort, AgentUnavailableError
from agentic.application.port.outbound.sse_queue_port import SSEQueuePort
from agentic.domain.model.agent_message import AgentMessage
from agentic.domain.model.agent_request import AgentRequest

_current_events: contextvars.ContextVar[SSEQueuePort | None] = contextvars.ContextVar(
    "current_events", default=None
)

AGENT_UNAVAILABLE_MESSAGE = (
    "The assistant is temporarily unavailable due to repeated upstream failures. "
    "Please try again in a moment."
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
        except AgentUnavailableError as exception:
            self._logger.warning(f"Agent unavailable while handling request: {exception}")
            await events.error(AGENT_UNAVAILABLE_MESSAGE)
        except Exception as exception:
            traceback.print_exc()
            traceback_str: str = "".join(traceback.format_exception(exception))
            await events.error(traceback_str)
        finally:
            _current_events.reset(context_events)
            await events.complete()
