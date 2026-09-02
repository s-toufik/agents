from pydantic import BaseModel, ConfigDict, Field

from agentic.adapter.outbound.agent.graph.schema.conversation import Conversation
from agentic.adapter.outbound.agent.graph.schema.planner_decision import PlannerDecision
from agentic.adapter.outbound.agent.graph.schema.reflection_decision import ReflectionDecision


class AgentState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    conversation: Conversation = Field(default_factory=Conversation)
    planner: PlannerDecision | None = None
    reflection: ReflectionDecision | None = None
    last_node: str = ""
    session_id: str = ""
    iteration: int = 0
    max_iterations: int = 20
    final_answer: str | None = None
