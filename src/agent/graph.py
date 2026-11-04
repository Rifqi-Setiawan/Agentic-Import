"""LangGraph orchestration over operational, persisted analysis services."""
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from src.services import analysis


class ShipmentAnalysisState(TypedDict, total=False):
    shipment_id: str
    company_id: str
    run_id: str
    mode: str
    event_type: str
    input_version: int
    target_item_ids: list[str] | None
    steps_log: list[dict[str, Any]]
    shipment: dict[str, Any]
    items: list[dict[str, Any]]
    documents: list[dict[str, Any]]
    plan: dict[str, Any]
    outcome: str
    readiness_status: str


def guarded(function):
    def node(state):
        try:
            return function(state)
        except Exception as error:
            with analysis.connect(state) as repo:
                repo.execute("UPDATE shipments SET status='failed',readiness_status='blocked' WHERE id=%s AND company_id=%s AND status NOT IN ('submitted','arrived')", repo.scope)
                repo.trace("error", "Analisis berhenti; hasil sebelumnya tetap tersimpan.", {"node": function.__name__, "error_type": type(error).__name__, "message": str(error)[:400]})
            raise
    return node


def build_analysis_graph():
    graph = StateGraph(ShipmentAnalysisState)
    nodes = [analysis.load_context, analysis.extract_documents, analysis.extract_items,
             analysis.plan_shipment, analysis.classify_items, analysis.verify_consistency,
             analysis.compliance, analysis.resolve_gaps, analysis.finalize]
    for node in nodes:
        graph.add_node(node.__name__, guarded(node))
    graph.set_entry_point(nodes[0].__name__)
    for previous, following in zip(nodes, nodes[1:]):
        graph.add_edge(previous.__name__, following.__name__)
    graph.add_edge(nodes[-1].__name__, END)
    # Durable business checkpoints are committed by each node. A recovered worker
    # reruns the pass idempotently; this MVP does not claim LangGraph PostgresSaver.
    return graph.compile()
