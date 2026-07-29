import asyncio
import contextvars
import json
import uuid
from contextlib import asynccontextmanager
from typing import Optional, cast

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from langgraph.checkpoint.memory import MemorySaver
from starlette.middleware.cors import CORSMiddleware

from agentic.agent.build_agent import build_agent
from agentic.agent.enum.role import Role
from agentic.agent.graph.schema.agent_state import AgentState

from agentic.agent.graph.schema.conversation_message import ConversationMessage

from agentic.agent.service.state_serialization import _unpack, _pack

from agentic.agent.tool.tool_registery import ToolRegistry
from agentic.agent.tool.code.python_tool_capability import PythonToolCapability
from agentic.agent.tool.sql.sql_tool_capability import SQLToolCapability
from agentic.bootstrap.container import Container
from agentic.infrastructure.app_configuration.enum.connector_type import ConnectorType
from agentic.infrastructure.app_configuration.model.configuration import AppConfiguration
from agentic.infrastructure.app_configuration.model.connector import DatabaseConnector
from agentic.infrastructure.code_sandbox.python.factory import SafeCodeFactory
from agentic.infrastructure.http.adapter.httpx.httpx_factory import HttpxFactory
from agentic.infrastructure.repository.repository import RepositoryFactory, AsyncSQLRepository
from agentic.infrastructure.repository.sql.factory import SQLHandlerFactory
from agentic.infrastructure.repository.sqlite.factory import SQLiteRepositoryFactory
from agentic.infrastructure.repository.sqlite.mapper import SettingsMapper
from agentic.infrastructure.repository.sqlite.settings import SqliteSettings

_current_queue: contextvars.ContextVar[Optional[asyncio.Queue]] = contextvars.ContextVar(
    "current_queue", default=None
)


async def on_token(token: str):
    queue = _current_queue.get()

    if queue:
        await queue.put(token)


@asynccontextmanager
async def lifespan(app: FastAPI):
    container = Container()
    is_on, exception = await container.boot
    configuration: AppConfiguration = container.application_configuration

    sqlite_connector: DatabaseConnector = cast(
        DatabaseConnector, configuration.connector.get(ConnectorType.database).get("sqlite")
    )
    sqlite_settings = SqliteSettings(SettingsMapper(sqlite_connector)())
    sqlite_factory: RepositoryFactory = SQLiteRepositoryFactory(sqlite_settings)
    sqlite_repository: AsyncSQLRepository = await sqlite_factory.create_repository()

    client = HttpxFactory().instance_async_http_client

    llm = ChatOpenAI(
        base_url="http://nautilus:1234/v1",
        api_key="lm_studio",
        model="mistralai/ministral-3-3b",
        http_async_client=client,
    )

    tool_registry = ToolRegistry(
        [
            SQLToolCapability(sqlite_repository, SQLHandlerFactory()),
            PythonToolCapability(SafeCodeFactory()),
        ]
    )

    checkpointer = MemorySaver()

    graph, _ = build_agent(
        llm=llm,
        tool_registry=tool_registry,
        checkpointer=checkpointer,
        use_streaming=True,
        on_token=on_token,
    )

    app.state.graph = graph
    app.state.checkpointer = checkpointer

    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    session_id: str
    message: str


@app.post("/session/start")
async def start_session():

    return {"session_id": str(uuid.uuid4())}


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):

    graph = app.state.graph

    config = {"configurable": {"thread_id": request.session_id}}

    snapshot = await graph.aget_state(config)

    if snapshot.values:
        state = _unpack(snapshot.values)
    else:
        state = AgentState(session_id=request.session_id)

    state.iteration = 0
    state.conversation.append(ConversationMessage(role=Role.USER, content=request.message))
    queue: asyncio.Queue[str | dict | None] = asyncio.Queue()

    async def run_agent():

        token = _current_queue.set(queue)

        try:
            result = await graph.ainvoke(_pack(state), config=config)
            final_state = _unpack(result)
            print(
                "FINAL STATE:",
                final_state
            )

            await queue.put({"type": "final", "answer": final_state.final_answer})

        except Exception as e:
            await queue.put({"type": "error", "message": str(e)})

        finally:
            _current_queue.reset(token)

            await queue.put(None)

    task = asyncio.create_task(run_agent())

    async def event_generator():

        try:
            while True:
                item = await queue.get()

                if item is None:
                    yield "event: done\ndata: {}\n\n"

                    break

                # Planner streamed token
                if isinstance(item, str):
                    yield f"event: token\ndata: {json.dumps({'token': item})}\n\n"

                # Final answer / errors
                elif isinstance(item, dict):
                    if item.get("type") == "final":
                        yield f"event: final\ndata: {json.dumps(item)}\n\n"

                    elif item.get("type") == "error":
                        yield f"event: error\ndata: {json.dumps(item)}\n\n"

        finally:
            await task

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
