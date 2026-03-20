# Handles the /query endpoint — sends user question to the agent and returns the answer
from fastapi import APIRouter
from langchain_core.messages import HumanMessage

from src.agent import memory
from src.agent.graph import build_agent_graph
from src.api.models import QueryRequest, QueryResponse, SessionClearResponse

router = APIRouter(tags=["agent"])


@router.post("/query", response_model=QueryResponse)
async def query_cluster(request: QueryRequest):
    print(f"Query received: {request.query}")

    graph = build_agent_graph()

    # Load previous messages so the agent remembers the conversation
    history = memory.get_history(request.session_id)
    messages = history + [HumanMessage(content=request.query)]

    result = await graph.ainvoke({"messages": messages})
    answer = result["messages"][-1].content

    # Save this exchange so follow-up questions have context
    memory.add_exchange(request.session_id, request.query, answer)

    return QueryResponse(query=request.query, answer=answer, session_id=request.session_id)


@router.delete("/sessions/{session_id}", response_model=SessionClearResponse)
async def clear_session(session_id: str):
    memory.clear_session(session_id)
    return SessionClearResponse(session_id=session_id, message="Session history cleared.")
