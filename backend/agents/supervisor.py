import logging
from typing import Annotated, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

logger = logging.getLogger(__name__)


class TriageState(TypedDict):
    incident: str
    trace_id: str
    log_analysis: str
    runbook_match: str
    incident_history: str
    remediation: str
    status: str
    _completed: Annotated[list[str], lambda a, b: list(set(a + b))]


# ─── Specialist node functions ────────────────────────────────────────────────

def _log_analyst_node(state: TriageState, config: RunnableConfig) -> dict:
    from agents.log_analyst import LogAnalystAgent

    tid = state.get("trace_id") or config.get("configurable", {}).get("trace_id", "")
    output = LogAnalystAgent().run(state["incident"], tid)
    return {"log_analysis": output, "_completed": ["log_analyst"]}


def _runbook_rag_node(state: TriageState, config: RunnableConfig) -> dict:
    from agents.runbook_rag import RunbookRAGAgent

    tid = state.get("trace_id") or config.get("configurable", {}).get("trace_id", "")
    output = RunbookRAGAgent().run(state["incident"], tid)
    return {"runbook_match": output, "_completed": ["runbook_rag"]}


def _incident_history_node(state: TriageState, config: RunnableConfig) -> dict:
    from agents.incident_history import IncidentHistoryAgent

    tid = state.get("trace_id") or config.get("configurable", {}).get("trace_id", "")
    output = IncidentHistoryAgent().run(state["incident"], tid)
    return {"incident_history": output, "_completed": ["incident_history"]}


def _remediation_node(state: TriageState, config: RunnableConfig) -> dict:
    from agents.remediation import RemediationAgent

    tid = state.get("trace_id") or config.get("configurable", {}).get("trace_id", "")
    output = RemediationAgent().run(
        incident=state["incident"],
        log_analysis=state.get("log_analysis", ""),
        runbook_match=state.get("runbook_match", ""),
        incident_history=state.get("incident_history", ""),
        trace_id=tid,
    )
    return {"remediation": output, "status": "complete", "_completed": ["remediation"]}


def _supervisor_node(state: TriageState) -> dict:
    """Supervisor: inspects state and optionally adjusts the incident before fan-out."""
    log = state.get("log_analysis", "")
    completed = state.get("_completed", [])

    if "log_analyst" in completed and "no" in log.lower() and "found" in log.lower():
        logger.warning(
            "[trace=%s] Supervisor: log_analyst found no data — widening time window",
            state.get("trace_id"),
        )
        return {
            "incident": state["incident"] + "\n[Supervisor note: extend log search to 6h window]",
            "status": "routing",
        }

    return {"status": "routing"}


# ─── Routing ─────────────────────────────────────────────────────────────────

def _route_after_supervisor(state: TriageState) -> list[str]:
    return ["log_analyst", "runbook_rag", "incident_history"]


# ─── Graph builder ────────────────────────────────────────────────────────────

def build_supervisor_graph() -> StateGraph:
    builder = StateGraph(TriageState)

    builder.add_node("supervisor", _supervisor_node)
    builder.add_node("log_analyst", _log_analyst_node)
    builder.add_node("runbook_rag", _runbook_rag_node)
    builder.add_node("incident_history", _incident_history_node)
    builder.add_node("remediation", _remediation_node)

    builder.add_edge(START, "supervisor")
    builder.add_conditional_edges(
        "supervisor",
        _route_after_supervisor,
        {
            "log_analyst": "log_analyst",
            "runbook_rag": "runbook_rag",
            "incident_history": "incident_history",
        },
    )

    for specialist in ("log_analyst", "runbook_rag", "incident_history"):
        builder.add_edge(specialist, "remediation")

    builder.add_edge("remediation", END)

    return builder.compile()
