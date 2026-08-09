from typing import Optional

from pydantic import BaseModel, Field

from agentic.adapter.outbound.agent.graph.schema.tool_call import ToolCall


class PlannerDecision(BaseModel):
    tool_calls: list[ToolCall] = Field(default_factory=list)
    answer: Optional[str] = None

    @property
    def wants_tools(self) -> bool:
        return len(self.tool_calls) > 0
