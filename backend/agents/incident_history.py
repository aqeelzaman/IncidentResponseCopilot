import logging
import os

from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

from tools.pinecone_tool import search_incidents

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are an incident historian with deep knowledge of past production incidents. "
    "Given an incident description:\n"
    "1. Search for the 3 most similar past incidents using search_incidents.\n"
    "2. For each match, extract: root cause, resolution, and duration.\n"
    "3. Return a structured analysis:\n"
    "   (1) Root cause for each similar incident\n"
    "   (2) How it was resolved\n"
    "   (3) How long it took\n"
    "   (4) Any patterns across the incidents\n"
    "Highlight if multiple past incidents share the same root cause — this strongly "
    "suggests the current incident has the same cause."
)


class IncidentHistoryAgent:
    def __init__(self) -> None:
        self._llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,
            api_key=os.environ.get("GROQ_API_KEY"),
        )
        self._agent = create_react_agent(
            self._llm,
            [search_incidents],
        )

    def run(self, incident: str, trace_id: str) -> str:
        logger.info("[trace=%s] IncidentHistoryAgent starting", trace_id)
        try:
            result = self._agent.invoke(
                {"messages": [("system", _SYSTEM_PROMPT), ("user", incident)]},
                config={"metadata": {"trace_id": trace_id}},
            )
            output = result["messages"][-1].content
            logger.info("[trace=%s] IncidentHistoryAgent complete", trace_id)
            return output
        except Exception as exc:
            logger.error("[trace=%s] IncidentHistoryAgent error: %s", trace_id, exc)
            return f"Incident history search failed: {exc}"
