from dataclasses import dataclass, field
from typing import Optional

from agentic.agent.enum.role import Role
from agentic.agent.tool.schema.tool_call import ToolCall


@dataclass
class ConversationMessage:
    role: Role
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_call_id: Optional[str] = None
