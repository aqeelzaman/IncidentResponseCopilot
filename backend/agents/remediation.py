import logging
import os
from textwrap import dedent

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class RemediationOutput(BaseModel):
    root_cause: str
    immediate_actions: list[str]
    followup_actions: list[str]
    confidence: float
    reasoning: str


_DRAFT_SYSTEM = dedent("""
    You are a senior SRE performing root-cause analysis and incident remediation.
    You will be given outputs from three specialist agents:
    - Log Analyst: anomaly data from BigQuery
    - Runbook RAG: relevant runbook sections from the knowledge base
    - Incident History: similar past incidents

    Your task (Step 1 - DRAFT):
    Generate 3 candidate remediation plans, ranked by your confidence (highest first).
    For each plan include:
    - Root cause hypothesis (1 sentence)
    - Confidence score (0.0–1.0)
    - Immediate actions (numbered list)
    - Key assumptions this plan relies on

    Format as:
    PLAN 1 (confidence: 0.XX):
    Root cause: ...
    Immediate actions:
    1. ...
    Assumptions: ...

    PLAN 2 ...
    PLAN 3 ...
""").strip()

_CRITIQUE_SYSTEM = dedent("""
    You are a critical reviewer. Given 3 remediation plans, for each one:
    - List 2-3 failure modes (what could go wrong if this plan is wrong)
    - Rate plan quality: HIGH / MEDIUM / LOW
    - Identify which plan has the strongest evidence support

    Be direct and specific. Reference the data provided.
""").strip()

_REFINE_SYSTEM = dedent("""
    You are a senior SRE making a final remediation recommendation.
    Given 3 candidate plans and their critiques, produce a FINAL RECOMMENDATION.

    Return ONLY valid JSON matching this schema:
    {
      "root_cause": "<one sentence>",
      "immediate_actions": ["<step 1>", "<step 2>", ...],
      "followup_actions": ["<follow-up 1>", "<follow-up 2>", ...],
      "confidence": <float 0.0-1.0>,
      "reasoning": "<2-3 sentences explaining why this was chosen>"
    }
""").strip()


class RemediationAgent:
    def __init__(self) -> None:
        self._llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,
            api_key=os.environ.get("GROQ_API_KEY"),
        )

    def _call(self, system: str, user: str, trace_id: str) -> str:
        response = self._llm.invoke(
            [SystemMessage(content=system), HumanMessage(content=user)],
            config={"metadata": {"trace_id": trace_id}},
        )
        return response.content  # type: ignore[return-value]

    def run(
        self,
        incident: str,
        log_analysis: str,
        runbook_match: str,
        incident_history: str,
        trace_id: str,
    ) -> str:
        logger.info("[trace=%s] RemediationAgent starting", trace_id)

        combined = dedent(f"""
            INCIDENT DESCRIPTION:
            {incident}

            LOG ANALYSIS OUTPUT:
            {log_analysis}

            RUNBOOK RAG OUTPUT:
            {runbook_match}

            INCIDENT HISTORY OUTPUT:
            {incident_history}
        """).strip()

        # Step 1: Draft
        drafts = self._call(_DRAFT_SYSTEM, combined, trace_id)
        logger.debug("[trace=%s] Remediation drafts generated", trace_id)

        # Step 2: Critique
        critique_input = f"{combined}\n\n---\nCANDIDATE PLANS:\n{drafts}"
        critiques = self._call(_CRITIQUE_SYSTEM, critique_input, trace_id)
        logger.debug("[trace=%s] Remediation critiques generated", trace_id)

        # Step 3: Refine
        refine_input = (
            f"{combined}\n\n---\nCANDIDATE PLANS:\n{drafts}"
            f"\n\n---\nCRITIQUES:\n{critiques}"
        )
        final_json_str = self._call(_REFINE_SYSTEM, refine_input, trace_id)

        # Parse JSON — gracefully fall back to raw text
        try:
            import json

            # Strip markdown code fences if present
            clean = final_json_str.strip()
            if clean.startswith("```"):
                clean = "\n".join(clean.split("\n")[1:])
            if clean.endswith("```"):
                clean = "\n".join(clean.split("\n")[:-1])

            parsed = RemediationOutput(**json.loads(clean))
            actions_str = "\n".join(f"  {i+1}. {a}" for i, a in enumerate(parsed.immediate_actions))
            followup_str = "\n".join(f"  - {a}" for a in parsed.followup_actions)
            output = (
                f"ROOT CAUSE: {parsed.root_cause}\n\n"
                f"CONFIDENCE: {parsed.confidence:.2f}\n\n"
                f"IMMEDIATE ACTIONS:\n{actions_str}\n\n"
                f"FOLLOW-UP ACTIONS:\n{followup_str}\n\n"
                f"REASONING: {parsed.reasoning}"
            )
        except Exception:
            output = final_json_str

        logger.info("[trace=%s] RemediationAgent complete", trace_id)
        return output
