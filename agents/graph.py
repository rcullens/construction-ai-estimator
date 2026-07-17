"""
LangGraph construction for the full analysis pipeline.
"""

from __future__ import annotations
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agents.state import AgentState
from agents.nodes import (
    ingestion_node,
    spec_manual_node,
    drawing_analyst_node,
    trade_scope_node,
    completeness_auditor_node,
    refinement_node,
    finalize_node,
)


def should_continue(state: AgentState) -> str:
    if state.get("needs_refinement") and state.get("iteration", 0) < state.get("max_iterations", 2):
        return "refine"
    return "finalize"


def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("ingestion", ingestion_node)
    workflow.add_node("spec_manual", spec_manual_node)
    workflow.add_node("drawing_analyst", drawing_analyst_node)
    workflow.add_node("trade_scope", trade_scope_node)
    workflow.add_node("auditor", completeness_auditor_node)
    workflow.add_node("refine", refinement_node)
    workflow.add_node("finalize", finalize_node)

    workflow.set_entry_point("ingestion")
    workflow.add_edge("ingestion", "spec_manual")
    workflow.add_edge("spec_manual", "drawing_analyst")
    workflow.add_edge("drawing_analyst", "trade_scope")
    workflow.add_edge("trade_scope", "auditor")

    workflow.add_conditional_edges(
        "auditor",
        should_continue,
        {
            "refine": "refine",
            "finalize": "finalize",
        },
    )
    workflow.add_edge("refine", "auditor")
    workflow.add_edge("finalize", END)

    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)
