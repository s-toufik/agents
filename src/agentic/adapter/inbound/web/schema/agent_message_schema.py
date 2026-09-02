from pydantic import BaseModel

from agentic.domain.enum.agent_message_status import MessageStreamType
from agentic.domain.enum.agent_message_type import AgentMessageType


class AgentMessageSchema(BaseModel):
    session_id: str
    content: str
    metadata: dict[str, str | int | float] | None
    error: str | None = None
    message_status: MessageStreamType = MessageStreamType.FINAL
    message_type: AgentMessageType = AgentMessageType.TEXT

    def serialize(self) -> bytes:
        # SSE framing: one `event:` line (the type), one `data:` line carrying the
        # whole payload as JSON -- JSON escapes embedded newlines, so multi-line
        # blank line that terminates the event per the SSE spec.
        return f"event: {self.message_status.value}\ndata: {self.model_dump_json()}\n\n".encode()
