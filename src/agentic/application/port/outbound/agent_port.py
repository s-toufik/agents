from typing import Protocol

from agentic.domain.model.agent_message import AgentMessage
from agentic.domain.model.agent_request import AgentRequest


class AgentUnavailableError(Exception):
    """Raised by an AgentPort implementation when the agent's backing service
    (e.g. the LLM gateway) is failing for a retryable-later reason -- a
    connection failure, a timeout, a rate limit, a provider outage -- rather
    than a hard failure the caller should surface as-is.

    This is part of the port's contract, not a leak of whatever outbound
    technology a given adapter happens to use underneath (circuit breaker,
    connection pool, provider SDK, ...): implementations must translate their
    own infrastructure's "retry later" conditions into this type before it
    crosses the port boundary.
    """


class AgentPort(Protocol):
    async def run(self, request: AgentRequest) -> AgentMessage: ...
