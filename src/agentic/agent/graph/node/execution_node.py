import asyncio

from agentic.agent.enum.role import Role
from agentic.agent.graph.node.node import Node
from agentic.agent.graph.schema.agent_state import AgentState
from agentic.agent.graph.schema.conversation_message import ConversationMessage
from agentic.agent.graph.schema.graph_state import GraphState
from agentic.agent.tool.schema.tool_call import ToolCall
from agentic.agent.tool.schema.tool_result import ToolResult
from agentic.agent.tool.tool_registery import ToolRegistry


class ExecutorNode(Node):
    def __init__(self, tool_registry: ToolRegistry) -> None:
        self._tool_registry = tool_registry

    async def __call__(self, graph_state: GraphState) -> GraphState:
        state: AgentState = self._unpack(graph_state)

        last_assistant: ConversationMessage | None = state.conversation.last_assistant()
        if not last_assistant or not last_assistant.tool_calls:
            state.last_node = "executor"
            return self._pack(state)

        results: tuple[ToolResult, ...] = await asyncio.gather(
            *[self._run(tool_call) for tool_call in last_assistant.tool_calls]
        )

        for result in results:
            state.conversation.append(
                ConversationMessage(
                    role=Role.TOOL,
                    content=result.content,
                    tool_call_id=result.id,
                )
            )

        state.last_node = "executor"
        return self._pack(state)

    async def _run(self, tool_call: ToolCall) -> ToolResult:
        try:
            tool = self._tool_registry.get(tool_call.name)
            return await tool.execute(_call_id=tool_call.id, **tool_call.args)
        except KeyError:
            return ToolResult(
                id=tool_call.id, output="", error=f"Unknown tool: '{tool_call.name}'."
            )
        except Exception as exc:  # noqa: BLE001
            return ToolResult(id=tool_call.id, output="", error=str(exc))
