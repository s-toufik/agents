import asyncio

from agentic.adapter.outbound.agent.enum.role import Role
from agentic.adapter.outbound.agent.graph.node.node import Node
from agentic.adapter.outbound.agent.graph.schema.agent_state import AgentState
from agentic.adapter.outbound.agent.graph.schema.conversation_message import ConversationMessage
from agentic.adapter.outbound.agent.graph.schema.graph_state import GraphState
from agentic.adapter.outbound.agent.graph.schema.tool_call import ToolCall
from agentic.adapter.outbound.agent.tool.schema.tool_result import ToolResult
from agentic.adapter.outbound.agent.tool.tool_registery import ToolRegistry


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
            request = tool.args_schema(**tool_call.args)
            request.call_id = tool_call.id
            return await tool.execute(request)
        except KeyError:
            return ToolResult(
                tool_name=tool_call.name,
                id=tool_call.id,
                output="",
                error=f"Unknown tool: '{tool_call.name}'.",
            )
        except Exception as exception:
            return ToolResult(
                tool_name=tool_call.name, id=tool_call.id, output="", error=str(exception)
            )
