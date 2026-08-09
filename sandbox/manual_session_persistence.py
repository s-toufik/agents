from fastapi import FastAPI
from pydantic import BaseModel
from langgraph.checkpoint.memory import MemorySaver

from agentic.adapter.outbound.agent.build_agent import build_agent
from agentic.adapter.outbound.agent import Role
from agentic.adapter.outbound.agent.graph import AgentState
from agentic.adapter.outbound.agent.graph.schema.conversation_message import ConversationMessage
from agentic.adapter.outbound.agent.service.state_serialization import unpack_state, pack_state

app = FastAPI()
checkpointer = MemorySaver()
graph, _ = build_agent(planner_llm=my_llm, database=my_db, checkpointer=checkpointer)


class ChatRequest(BaseModel):
    session_id: str
    message: str


@app.post("/chat")
async def chat(req: ChatRequest):
    config = {"configurable": {"thread_id": req.session_id}}

    snapshot = await graph.aget_state(config)
    state = (
        unpack_state(snapshot.values) if snapshot.values else AgentState(session_id=req.session_id)
    )

    state.conversation.append(ConversationMessage(role=Role.USER, content=req.message))

    result_gs = await graph.ainvoke(pack_state(state), config=config)
    result = unpack_state(result_gs)

    return {"answer": result.final_answer, "iteration": result.iteration}
