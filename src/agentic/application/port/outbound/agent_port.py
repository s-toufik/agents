from typing import Protocol

from agentic.domain.model.agent_message import AgentMessage
from agentic.domain.model.agent_request import AgentRequest


class AgentPort(Protocol):
    async def run(self, request: AgentRequest) -> AgentMessage: ...
