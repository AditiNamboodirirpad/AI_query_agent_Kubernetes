# Returns a health score for the cluster plus an AI explanation
from fastapi import APIRouter, Query
from langchain_core.messages import HumanMessage

from src.agent.graph import build_agent_graph
from src.api.models import ClusterHealthResponse
from src.k8s import health as k8s_health

router = APIRouter(prefix="/cluster", tags=["cluster"])


@router.get("/health", response_model=ClusterHealthResponse)
async def cluster_health_overview(namespace: str = Query(default="default")):
    print(f"Health check requested for namespace: {namespace}")

    health_data = k8s_health.compute_cluster_health(namespace)

    # Ask the agent to explain the health report in plain English
    graph = build_agent_graph()
    prompt = (
        f"Here is the cluster health report for namespace '{namespace}':\n{health_data}\n\n"
        "Give a short summary and list the most important things to fix. Use bullet points."
    )
    result = await graph.ainvoke({"messages": [HumanMessage(content=prompt)]})
    ai_analysis = result["messages"][-1].content

    return ClusterHealthResponse(
        score=health_data["score"],
        status=health_data["status"],
        summary=health_data["summary"],
        issues=health_data["issues"],
        ai_analysis=ai_analysis,
    )
