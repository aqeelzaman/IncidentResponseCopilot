import logging
import os

from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

from tools.bigquery_tool import query_logs, query_metrics

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a log analysis expert for a production GCP environment. "
    "Given an incident description:\n"
    "1. Identify the affected service name.\n"
    "2. Query its ERROR/CRITICAL logs for the last 2 hours with query_logs.\n"
    "3. Query p99_latency, error_rate, and active_connections with query_metrics.\n"
    "4. Return a structured analysis:\n"
    "   (1) Error spike timeline — when errors started and frequency\n"
    "   (2) Top 3 anomalous metrics with specific values\n"
    "   (3) Affected service names\n"
    "Be concise. Cite specific log lines and metric values."
)


class LogAnalystAgent:
    def __init__(self) -> None:
        self._llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,
            api_key=os.environ.get("GROQ_API_KEY"),
        )
        self._agent = create_react_agent(
            self._llm,
            [query_logs, query_metrics],
        )

    def run(self, incident: str, trace_id: str) -> str:
        logger.info("[trace=%s] LogAnalystAgent starting", trace_id)
        try:
            result = self._agent.invoke(
                {"messages": [("system", _SYSTEM_PROMPT), ("user", incident)]},
                config={"metadata": {"trace_id": trace_id}},
            )
            output = result["messages"][-1].content
            logger.info("[trace=%s] LogAnalystAgent complete", trace_id)
            return output
        except Exception as exc:
            logger.error("[trace=%s] LogAnalystAgent error: %s", trace_id, exc)
            return f"Log analysis failed: {exc}"
