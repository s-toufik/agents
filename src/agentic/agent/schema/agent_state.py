from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from agentic.agent.schema.conversation import Conversation
from agentic.agent.schema.planner_decision import PlannerDecision
from agentic.agent.schema.reflection_decision import ReflectionDecision


class AgentState(BaseModel):

    model_config = ConfigDict(arbitrary_types_allowed=True)

    conversation:   Conversation           = Field(default_factory=Conversation)
    planner:        Optional[PlannerDecision]   = None
    reflection:     Optional[ReflectionDecision] = None
    last_node:      str                    = ""
    session_id:     str                    = ""
    iteration:      int                    = 0
    max_iterations: int                    = 6
    final_answer:   Optional[str]          = None