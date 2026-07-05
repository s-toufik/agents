from typing import TypedDict


class GraphState(TypedDict):
    state: dict  # AgentState.model_dump() result