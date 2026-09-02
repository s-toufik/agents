from typing import Protocol

from agentic.application.port.outbound.sse_queue_port import SSEQueuePort
from agentic.domain.model.agent_request import AgentRequest


class StreamAgentPort(Protocol):
    async def execute(self, request: AgentRequest, events: SSEQueuePort) -> None: ...
