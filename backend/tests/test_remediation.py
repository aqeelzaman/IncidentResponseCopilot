import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import pytest
from unittest.mock import MagicMock, patch, call


SAMPLE_LOG_ANALYSIS = "847 ERROR logs in last 2h. p99_latency=4247ms. Service: checkout-service."
SAMPLE_RUNBOOK = "DB Connection Pool Exhaustion runbook. Fix: increase pool_size to 50."
SAMPLE_HISTORY = "2 similar past incidents both caused by DB connection pool exhaustion."


def _make_llm_response(content: str) -> MagicMock:
    msg = MagicMock()
    msg.content = content
    return msg


def test_remediation_three_step_chain(sample_incident, sample_trace_id):
    draft_output = (
        "PLAN 1 (confidence: 0.91):\nRoot cause: DB connection pool exhausted\n"
        "Immediate actions:\n1. Increase pool_size to 50\nAssumptions: DB is healthy"
    )
    critique_output = "PLAN 1: HIGH quality. Supported by log data and 2 historical incidents."
    final_output = json.dumps({
        "root_cause": "DB connection pool exhausted (pool_size=10 insufficient for current load)",
        "immediate_actions": [
            "Increase pool_size from 10 to 50 in db_config ConfigMap",
            "Restart checkout-service deployment",
            "Monitor error rate recovery on Grafana",
        ],
        "followup_actions": [
            "Add connection pool utilization alert (threshold: >85%)",
            "Deploy PgBouncer as long-term solution",
        ],
        "confidence": 0.91,
        "reasoning": "847 ERROR logs with pool exhaustion messages. 2/2 similar past incidents had same root cause. Runbook confirms fix.",
    })

    with patch("langchain_groq.ChatGroq.__init__", return_value=None):
        from agents.remediation import RemediationAgent

        agent = RemediationAgent.__new__(RemediationAgent)
        agent._llm = MagicMock()
        agent._llm.invoke.side_effect = [
            _make_llm_response(draft_output),
            _make_llm_response(critique_output),
            _make_llm_response(final_output),
        ]

        result = agent.run(
            incident=sample_incident,
            log_analysis=SAMPLE_LOG_ANALYSIS,
            runbook_match=SAMPLE_RUNBOOK,
            incident_history=SAMPLE_HISTORY,
            trace_id=sample_trace_id,
        )

    assert "ROOT CAUSE" in result
    assert "CONFIDENCE" in result
    assert "IMMEDIATE ACTIONS" in result
    assert "0.91" in result
    assert agent._llm.invoke.call_count == 3


def test_remediation_falls_back_on_bad_json(sample_incident, sample_trace_id):
    with patch("langchain_groq.ChatGroq.__init__", return_value=None):
        from agents.remediation import RemediationAgent

        agent = RemediationAgent.__new__(RemediationAgent)
        agent._llm = MagicMock()
        agent._llm.invoke.side_effect = [
            _make_llm_response("PLAN 1: ..."),
            _make_llm_response("HIGH quality"),
            _make_llm_response("This is not valid JSON at all."),
        ]

        result = agent.run(
            incident=sample_incident,
            log_analysis="some analysis",
            runbook_match="some runbook",
            incident_history="some history",
            trace_id=sample_trace_id,
        )

    # Should return the raw LLM text rather than crashing
    assert result == "This is not valid JSON at all."


def test_remediation_passes_trace_id(sample_incident, sample_trace_id):
    final_output = json.dumps({
        "root_cause": "test",
        "immediate_actions": ["step 1"],
        "followup_actions": ["followup 1"],
        "confidence": 0.8,
        "reasoning": "test reasoning",
    })

    with patch("langchain_groq.ChatGroq.__init__", return_value=None):
        from agents.remediation import RemediationAgent

        agent = RemediationAgent.__new__(RemediationAgent)
        agent._llm = MagicMock()
        agent._llm.invoke.side_effect = [
            _make_llm_response("draft"),
            _make_llm_response("critique"),
            _make_llm_response(final_output),
        ]

        agent.run(
            incident=sample_incident,
            log_analysis="analysis",
            runbook_match="runbook",
            incident_history="history",
            trace_id=sample_trace_id,
        )

    for c in agent._llm.invoke.call_args_list:
        config = c[1].get("config", {})
        assert config.get("metadata", {}).get("trace_id") == sample_trace_id
