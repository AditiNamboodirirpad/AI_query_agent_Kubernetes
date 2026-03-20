# Builds the LangGraph agent that powers the AI assistant
# The agent follows a loop: think → call a tool → think again → give answer
from functools import lru_cache
from typing import Literal

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from src.agent.prompts import SYSTEM_PROMPT
from src.agent.tools import ALL_TOOLS
from src.config import get_settings


def _route(state: MessagesState) -> Literal["tools", "__end__"]:
    # If Claude wants to call a tool, go to tools node — otherwise we're done
    last = state["messages"][-1]
    if getattr(last, "tool_calls", None):
        return "tools"
    return END


# Build once and cache — no need to rebuild on every request
@lru_cache(maxsize=1)
def build_agent_graph():
    settings = get_settings()

    # Attach all K8s tools to Claude so it can call them
    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=settings.anthropic_api_key,
        temperature=0,
    ).bind_tools(ALL_TOOLS)

    tool_node = ToolNode(ALL_TOOLS)

    def call_model(state: MessagesState):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        response = llm.invoke(messages)
        return {"messages": [response]}

    # Wire up the graph: agent calls tools until it has enough info to answer
    workflow = StateGraph(MessagesState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", _route)
    workflow.add_edge("tools", "agent")

    return workflow.compile()
