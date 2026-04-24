import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import MagicMock, patch


def _make_agent_result(content: str) -> dict:
    msg = MagicMock()
    msg.content = content
    return {"messages": [msg]}


def test_log_analyst_returns_output(sample_incident, sample_trace_id):
    expected = "847 ERROR logs. p99_latency=4247ms. Affected: checkout-service."

    from agents.log_analyst import LogAnalystAgent

    agent = LogAnalystAgent.__new__(LogAnalystAgent)
    agent._agent = MagicMock()
    agent._agent.invoke.return_value = _make_agent_result(expected)

    result = agent.run(sample_incident, sample_trace_id)
    assert result == expected


def test_log_analyst_handles_exception(sample_incident, sample_trace_id):
    from agents.log_analyst import LogAnalystAgent

    agent = LogAnalystAgent.__new__(LogAnalystAgent)
    agent._agent = MagicMock()
    agent._agent.invoke.side_effect = Exception("BQ unavailable")

    result = agent.run(sample_incident, sample_trace_id)
    assert "failed" in result.lower() or "error" in result.lower()


def test_log_analyst_passes_trace_id(sample_incident, sample_trace_id):
    from agents.log_analyst import LogAnalystAgent

    agent = LogAnalystAgent.__new__(LogAnalystAgent)
    agent._agent = MagicMock()
    agent._agent.invoke.return_value = _make_agent_result("analysis")

    agent.run(sample_incident, sample_trace_id)

    call_kwargs = agent._agent.invoke.call_args
    config = call_kwargs[1].get("config", {}) if call_kwargs[1] else {}
    assert config.get("metadata", {}).get("trace_id") == sample_trace_id
