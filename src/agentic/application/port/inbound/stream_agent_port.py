from typing import Protocol

from agentic.application.port.outbound.stream_events_port import StreamEventsPort
from agentic.domain.model.agent_request import AgentRequest


class StramAgentPort(Protocol):
    async def execute(self, request: AgentRequest, events: StreamEventsPort) -> None: ...
