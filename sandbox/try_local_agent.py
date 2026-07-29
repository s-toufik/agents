import asyncio
from pprint import pprint

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel

from agentic.agent.enum.role import Role
from agentic.agent.graph.schema.agent_state import AgentState
from agentic.agent.graph.schema.conversation_message import ConversationMessage
from agentic.agent.service.state_serialization import _unpack, _pack
from agentic.agent.tool.code.python_tool_capability import PythonToolCapability
from agentic.agent.tool.tool_registery import ToolRegistry
from agentic.infrastructure.code_sandbox.python.factory import SafeCodeFactory
from agentic.infrastructure.http.adapter.httpx.httpx_factory import HttpxFactory
from src.agentic.agent.build_agent import build_agent

class ChatRequest(BaseModel):
    session_id: str
    message: str

async def main():
    client = HttpxFactory().instance_async_http_client

    llm = ChatOpenAI(
        base_url="http://nautilus:1234/v1",
        api_key="lm_studio",
        model="mistralai/ministral-3-3b",
        http_async_client=client,
    )

    tool_registry = ToolRegistry(
        [
            PythonToolCapability(SafeCodeFactory()),
        ]
    )

    checkpointer = (
        MemorySaver()
    )

    graph, _ = build_agent(llm=llm, tool_registry=tool_registry, checkpointer=checkpointer)

    print("Chat started (type 'exit' to quit)\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() == "exit":
            break

        req: ChatRequest = ChatRequest(session_id="test", message=user_input)
        config = {"configurable": {"thread_id": req.session_id}}

        snapshot = await graph.aget_state(config)
        state = _unpack(snapshot.values) if snapshot.values else AgentState(session_id=req.session_id)

        state.conversation.append(ConversationMessage(role=Role.USER, content=req.message))

        result_gs = await graph.ainvoke(_pack(state), config=config)
        result = _unpack(result_gs)

        pprint({"answer": result.final_answer, "iteration": result.iteration})

if __name__ == "__main__":
    asyncio.run(main())

