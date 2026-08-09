import asyncio
from pprint import pprint

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel

from agentic.adapter.outbound.agent import Role
from agentic.adapter.outbound.agent.graph import AgentState
from agentic.adapter.outbound.agent.graph.schema.conversation_message import ConversationMessage
from agentic.adapter.outbound.agent.service.state_serialization import unpack_state, pack_state
from agentic.adapter.outbound.agent.tool.code.python_tool_capability import PythonToolCapability
from agentic.adapter.outbound.agent.tool.sql.sql_tool_capability import SQLToolCapability
from agentic.adapter.outbound.agent import ToolRegistry
from agentic_application.bootstrap.container import Container
from agentic_core.infrastructure.application_configuration.model.configuration import (
    ApplicationConfiguration,
)
from agentic_core.infrastructure.application_configuration.model.connector import DatabaseConnector
from agentic_core.infrastructure.runtime import SafeCodeFactory
from agentic_core.infrastructure.http.adapter.httpx.factory import HttpxFactory
from agentic_core.infrastructure.repository.sql.factory import SQLHandlerFactory
from agentic.adapter.outbound.agent.build_agent import build_agent
from agentic_core.infrastructure.repository import RepositoryFactory, AsyncSQLRepository
from agentic_core.infrastructure.repository.sqlite.factory import SQLiteRepositoryFactory
from agentic_core.infrastructure.repository.sqlite.mapper import SqliteSettingsMapper
from typing import cast
from agentic_core.infrastructure.repository.sqlite import SqliteSettings
from agentic_core.infrastructure.application_configuration.enum.connector_type import ConnectorType


async def on_token(token: str):
    print(token, end="", flush=True)


class ChatRequest(BaseModel):
    session_id: str
    message: str


async def main():
    container = Container()
    is_on, exception = await container.boot
    configuration: ApplicationConfiguration = container.application_configuration

    sqlite_connector: DatabaseConnector = cast(
        DatabaseConnector, configuration.connector.get(ConnectorType.database).get("sqlite")
    )
    sqlite_settings = SqliteSettings(SqliteSettingsMapper(sqlite_connector)())
    sqlite_factory: RepositoryFactory = SQLiteRepositoryFactory(sqlite_settings)
    sqlite_repository: AsyncSQLRepository = await sqlite_factory.connect()

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
        planner_llm=llm,
        tool_registry=tool_registry,
        checkpointer=checkpointer,
        use_streaming=True,
        on_token=on_token,
    )

    print("Chat started (type 'exit' to quit)\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() == "exit":
            break

        req: ChatRequest = ChatRequest(session_id="test", message=user_input)
        config = {"configurable": {"thread_id": req.session_id}}

        snapshot = await graph.aget_state(config)
        state = (
            unpack_state(snapshot.values)
            if snapshot.values
            else AgentState(session_id=req.session_id)
        )
        state.iteration = 0

        state.conversation.append(ConversationMessage(role=Role.USER, content=req.message))

        result_gs = await graph.ainvoke(pack_state(state), config=config)
        result = unpack_state(result_gs)

        pprint({"answer": result.final_answer, "iteration": result.iteration})


if __name__ == "__main__":
    asyncio.run(main())
