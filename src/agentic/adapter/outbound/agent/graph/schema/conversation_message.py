from dataclasses import dataclass, field

from agentic.adapter.outbound.agent.enum.role import Role
from agentic.adapter.outbound.agent.graph.schema.tool_call import ToolCall


@dataclass
class ConversationMessage:
    role: Role
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_call_id: str | None = None
