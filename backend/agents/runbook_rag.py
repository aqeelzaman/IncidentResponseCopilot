import logging
import os

from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

from tools.pinecone_tool import search_runbooks

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are an SRE runbook expert. Given an incident description:\n"
    "1. Search for relevant runbook sections using search_runbooks.\n"
    "2. If you identify the affected service, search again with a service_tag filter.\n"
    "3. Return a structured response:\n"
    "   (1) Runbook name matched\n"
    "   (2) Recommended diagnostic steps (quoted from runbook)\n"
    "   (3) Recommended fix steps (quoted from runbook)\n"
    "Quote exact runbook text where relevant. Be specific and actionable."
)


class RunbookRAGAgent:
    def __init__(self) -> None:
        self._llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,
            api_key=os.environ.get("GROQ_API_KEY"),
        )
        self._agent = create_react_agent(
            self._llm,
            [search_runbooks],
        )

    def run(self, incident: str, trace_id: str) -> str:
        logger.info("[trace=%s] RunbookRAGAgent starting", trace_id)
        try:
            result = self._agent.invoke(
                {"messages": [("system", _SYSTEM_PROMPT), ("user", incident)]},
                config={"metadata": {"trace_id": trace_id}},
            )
            output = result["messages"][-1].content
            logger.info("[trace=%s] RunbookRAGAgent complete", trace_id)
            return output
        except Exception as exc:
            logger.error("[trace=%s] RunbookRAGAgent error: %s", trace_id, exc)
            return f"Runbook search failed: {exc}"
