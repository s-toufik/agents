from fastapi import FastAPI
from pydantic import BaseModel
from langgraph.checkpoint.memory import MemorySaver

from src.agentic.agent.build_agent import build_agent
from src.agentic.agent.enum.role import Role
from agentic.agent.graph.schema.agent_state import AgentState
from agentic.agent.graph.schema.conversation_message import ConversationMessage
from src.agentic.agent.service.state_serialization import _unpack, _pack

app = FastAPI()
checkpointer = MemorySaver()
graph, _ = build_agent(llm=my_llm, database=my_db, checkpointer=checkpointer)


class ChatRequest(BaseModel):
    session_id: str
    message: str


@app.post("/chat")
async def chat(req: ChatRequest):
    config = {"configurable": {"thread_id": req.session_id}}

    snapshot = await graph.aget_state(config)
    state = _unpack(snapshot.values) if snapshot.values else AgentState(session_id=req.session_id)

    state.conversation.append(ConversationMessage(role=Role.USER, content=req.message))

    result_gs = await graph.ainvoke(_pack(state), config=config)
    result = _unpack(result_gs)

    return {"answer": result.final_answer, "iteration": result.iteration}
