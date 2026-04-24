import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import MagicMock


def _make_agent_result(content: str) -> dict:
    msg = MagicMock()
    msg.content = content
    return {"messages": [msg]}


def test_runbook_rag_returns_output(sample_incident, sample_trace_id):
    expected = "Runbook: DB Connection Pool Exhaustion. Fix: increase pool_size to 50."

    from agents.runbook_rag import RunbookRAGAgent

    agent = RunbookRAGAgent.__new__(RunbookRAGAgent)
    agent._agent = MagicMock()
    agent._agent.invoke.return_value = _make_agent_result(expected)

    assert agent.run(sample_incident, sample_trace_id) == expected


def test_runbook_rag_handles_no_results(sample_incident, sample_trace_id):
    from agents.runbook_rag import RunbookRAGAgent

    agent = RunbookRAGAgent.__new__(RunbookRAGAgent)
    agent._agent = MagicMock()
    agent._agent.invoke.return_value = _make_agent_result("No relevant runbook sections found.")

    result = agent.run(sample_incident, sample_trace_id)
    assert result != ""


def test_runbook_rag_passes_trace_id(sample_incident, sample_trace_id):
    from agents.runbook_rag import RunbookRAGAgent

    agent = RunbookRAGAgent.__new__(RunbookRAGAgent)
    agent._agent = MagicMock()
    agent._agent.invoke.return_value = _make_agent_result("result")

    agent.run(sample_incident, sample_trace_id)

    call_kwargs = agent._agent.invoke.call_args
    config = call_kwargs[1].get("config", {}) if call_kwargs[1] else {}
    assert config.get("metadata", {}).get("trace_id") == sample_trace_id
