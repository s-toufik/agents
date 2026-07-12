import asyncio
import contextvars
import json
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langgraph.checkpoint.memory import MemorySaver

from agentic.agent.enum.role import Role
from agentic.agent.graph.agent_graph import AgentGraph
from agentic.agent.graph.node.execution_node import ExecutorNode
from agentic.agent.graph.node.feedback_node import FeedbackNode
from agentic.agent.graph.node.final_node import FinalNode
from agentic.agent.graph.node.memory_node import MemoryNode
from agentic.agent.graph.node.reflection_node import ReflectionNode
from agentic.agent.graph.node.router_node import RouterNode
from agentic.agent.graph.node.streaming_planner_node import StreamingPlannerNode
from agentic.agent.graph.schema.agent_state import AgentState
from agentic.agent.graph.schema.conversation_message import ConversationMessage
from agentic.agent.service.state_serialization import _unpack, _pack
from agentic.agent.tool.python_tool_capability import PythonToolCapability
from agentic.agent.tool.sql_tool_capability import SQLToolCapability
from agentic.agent.tool.tool_registery import ToolRegistry

_current_queue: contextvars.ContextVar[asyncio.Queue] = contextvars.ContextVar("current_queue")


async def on_token(tok: str) -> None:
    queue = _current_queue.get(None)
    if queue is not None:
        await queue.put(tok)


@asynccontextmanager
async def lifespan(app: FastAPI):
    my_llm = ...  # your real ChatModel instance
    my_db = ...  # your real DB adapter

    registry = ToolRegistry(
        [
            SQLToolCapability(my_db, default_dialect="oracle"),
            PythonToolCapability(),
        ]
    )

    app.state.checkpointer = MemorySaver()  # swap for AsyncSqliteSaver for durability
    app.state.graph = AgentGraph(
        planner=StreamingPlannerNode(my_llm, registry, on_token=on_token),
        router=RouterNode(),
        executor=ExecutorNode(registry),
        memory=MemoryNode(),
        reflection=ReflectionNode(my_llm),
        feedback=FeedbackNode(),
        final=FinalNode(),
    ).build(checkpointer=app.state.checkpointer)

    yield


app = FastAPI(lifespan=lifespan)


@app.post("/session/start")
async def start_session():
    return {"session_id": str(uuid.uuid4())}


class ChatRequest(BaseModel):
    session_id: str
    message: str


@app.get("/chat/stream")
async def chat_stream(session_id: str, message: str):
    graph = app.state.graph
    config = {"configurable": {"thread_id": session_id}}

    snapshot = await graph.aget_state(config)
    state = _unpack(snapshot.values) if snapshot.values else AgentState(session_id=session_id)
    state.conversation.append(ConversationMessage(role=Role.USER, content=message))

    queue: asyncio.Queue = asyncio.Queue()

    async def run_graph():
        token = _current_queue.set(queue)
        try:
            await graph.ainvoke(_pack(state), config=config)
        finally:
            _current_queue.reset(token)
            await queue.put(None)  # sentinel

    task = asyncio.create_task(run_graph())

    async def event_generator():
        while True:
            tok = await queue.get()
            if tok is None:
                yield "event: done\ndata: {}\n\n"
                break
            yield f"data: {json.dumps({'token': tok})}\n\n"
        await task

    return StreamingResponse(event_generator(), media_type="text/event-stream")
