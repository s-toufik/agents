from abc import ABC, abstractmethod

from agentic.agent.graph.schema.agent_state import AgentState
from agentic.agent.graph.schema.graph_state import GraphState
from agentic.agent.service.state_serialization import _unpack, _pack


class Node(ABC):
    @abstractmethod
    async def __call__(self, graph_state: GraphState) -> GraphState: ...

    @staticmethod
    def _unpack(graph_state: GraphState) -> AgentState:
        return _unpack(graph_state)

    @staticmethod
    def _pack(agent_state: AgentState) -> GraphState:
        return _pack(agent_state)
