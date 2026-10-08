from typing import Annotated, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


def echo_node(state: AgentState, config: RunnableConfig) -> dict:
    """Phase 1 stub node: confirm tenant/thread config wiring without LLM calls."""
    configurable = config.get("configurable") or {}
    tenant_id = configurable.get("tenant_id", "unknown")
    thread_id = configurable.get("thread_id", "unknown")
    last = state["messages"][-1]
    user_text = getattr(last, "content", str(last))
    reply = (
        f"[agent-service stub] tenant={tenant_id} thread={thread_id} "
        f"echo={user_text}"
    )
    return {"messages": [{"role": "assistant", "content": reply}]}


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("echo", echo_node)
    graph.add_edge(START, "echo")
    graph.add_edge("echo", END)
    return graph.compile()
