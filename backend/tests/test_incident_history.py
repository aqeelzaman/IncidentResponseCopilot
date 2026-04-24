import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import MagicMock


def _make_agent_result(content: str) -> dict:
    msg = MagicMock()
    msg.content = content
    return {"messages": [msg]}


def test_incident_history_returns_similar_incidents(sample_incident, sample_trace_id):
    expected = "2 similar past incidents both caused by DB connection pool exhaustion."

    from agents.incident_history import IncidentHistoryAgent

    agent = IncidentHistoryAgent.__new__(IncidentHistoryAgent)
    agent._agent = MagicMock()
    agent._agent.invoke.return_value = _make_agent_result(expected)

    assert agent.run(sample_incident, sample_trace_id) == expected


def test_incident_history_handles_no_matches(sample_incident, sample_trace_id):
    from agents.incident_history import IncidentHistoryAgent

    agent = IncidentHistoryAgent.__new__(IncidentHistoryAgent)
    agent._agent = MagicMock()
    agent._agent.invoke.return_value = _make_agent_result("No similar past incidents found.")

    assert agent.run(sample_incident, sample_trace_id) != ""


def test_incident_history_passes_trace_id(sample_incident, sample_trace_id):
    from agents.incident_history import IncidentHistoryAgent

    agent = IncidentHistoryAgent.__new__(IncidentHistoryAgent)
    agent._agent = MagicMock()
    agent._agent.invoke.return_value = _make_agent_result("history result")

    agent.run(sample_incident, sample_trace_id)

    call_kwargs = agent._agent.invoke.call_args
    config = call_kwargs[1].get("config", {}) if call_kwargs[1] else {}
    assert config.get("metadata", {}).get("trace_id") == sample_trace_id
