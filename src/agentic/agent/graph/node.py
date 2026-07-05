from abc import ABC, abstractmethod

from agentic.agent.schema.agent_state import AgentState
from agentic.agent.schema.graph_state import GraphState
from agentic.agent.service.state_serialization import _unpack, _pack


class Node(ABC):

    @abstractmethod
    async def __call__(self, gs: GraphState) -> GraphState: ...

    @staticmethod
    def _unpack(gs: GraphState) -> AgentState:
        return _unpack(gs)

    @staticmethod
    def _pack(state: AgentState) -> GraphState:
        return _pack(state)