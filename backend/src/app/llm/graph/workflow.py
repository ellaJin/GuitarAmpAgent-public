from typing import TypedDict, Any

from langgraph.graph import StateGraph, END
# from langgraph.checkpoint.sqlite import SqliteSaver

from guitar_fx_agent.config import MEMORY_DB_PATH
# from agents.deep_agent import build_deep_agent


# class AgentState(TypedDict, total=False):
#     messages: list[dict]
#     user_id: str
#
#
# def agent_node(state: AgentState) -> AgentState:
#     agent = build_deep_agent()
#     result = agent.invoke({"messages": state["messages"]})
#     return {"messages": result.get("messages", state["messages"])}


def build_graph():
    pass
    # builder = StateGraph(AgentState)
    # builder.add_node("agent", agent_node)
    # builder.set_entry_point("agent")
    # builder.set_finish_point("agent")
    #
    # checkpointer = SqliteSaver(str(MEMORY_DB_PATH))
    # graph = builder.compile(checkpointer=checkpointer)
    # return graph
