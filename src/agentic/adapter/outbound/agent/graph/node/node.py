from abc import ABC, abstractmethod

from agentic.adapter.outbound.agent.graph.schema.agent_state import AgentState
from agentic.adapter.outbound.agent.graph.schema.graph_state import GraphState
from agentic.adapter.outbound.agent.service.state_serialization import unpack_state, pack_state


class Node(ABC):
    @abstractmethod
    async def __call__(self, graph_state: GraphState) -> GraphState: ...

    @staticmethod
    def _unpack(graph_state: GraphState) -> AgentState:
        return unpack_state(graph_state)

    @staticmethod
    def _pack(agent_state: AgentState) -> GraphState:
        return pack_state(agent_state)
