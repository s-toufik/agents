from dataclasses import dataclass
from typing import Any

from agentic.domain.enum.agent_message_status import MessageStreamType


@dataclass(slots=True)
class AgentMessageStream:
    type: MessageStreamType
    content: str
    metadata: dict[str, Any] | None = None
