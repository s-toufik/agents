import asyncio

from agentic.agent.enum.role import Role
from agentic.agent.graph.node import Node
from agentic.agent.schema.conversation_message import ConversationMessage
from agentic.agent.schema.graph_state import GraphState
from agentic.agent.schema.tool_call import ToolCall
from agentic.agent.schema.tool_result import ToolResult
from agentic.agent.tools.tool_registery import ToolRegistry


class ExecutorNode(Node):

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    async def __call__(self, gs: GraphState) -> GraphState:
        state = self._unpack(gs)

        last_assistant = state.conversation.last_assistant()
        if not last_assistant or not last_assistant.tool_calls:
            state.last_node = "executor"
            return self._pack(state)

        async def _run(tc: ToolCall) -> ToolResult:
            try:
                tool = self._registry.get(tc.name)
                return await tool.execute(_call_id=tc.id, **tc.args)
            except KeyError:
                return ToolResult(id=tc.id, output="", error=f"Unknown tool: '{tc.name}'.")
            except Exception as exc:  # noqa: BLE001
                return ToolResult(id=tc.id, output="", error=str(exc))

        results: tuple[ToolResult, ...] = await asyncio.gather(
            *[_run(tc) for tc in last_assistant.tool_calls]
        )

        for result in results:
            state.conversation.append(ConversationMessage(
                role=Role.TOOL,
                content=result.content,
                tool_call_id=result.id,
            ))

        state.last_node = "executor"
        return self._pack(state)