import logging
import os
from typing import Optional

from langchain_core.tools import tool

from tools.embeddings import embed

logger = logging.getLogger(__name__)

_RUNBOOKS_INDEX = os.getenv("PINECONE_RUNBOOKS_INDEX", "runbooks")
_INCIDENTS_INDEX = os.getenv("PINECONE_INCIDENTS_INDEX", "incidents")

_pc = None


def _get_pinecone():
    global _pc
    if _pc is None:
        from pinecone import Pinecone  # type: ignore

        _pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    return _pc


@tool
def search_runbooks(query: str, service_tag: Optional[str] = None) -> str:
    """Semantic search over the runbooks Pinecone index.

    Returns the top-5 most relevant runbook chunks.  Pass service_tag to
    filter results to a specific service (e.g. 'checkout-service').
    """
    try:
        vec = embed(query)
        index = _get_pinecone().Index(_RUNBOOKS_INDEX)

        filter_dict = {"service_tag": {"$eq": service_tag}} if service_tag else None
        results = index.query(
            vector=vec,
            top_k=5,
            filter=filter_dict,
            include_metadata=True,
        )

        if not results.matches:
            return "No relevant runbook sections found."

        parts = []
        for match in results.matches:
            meta = match.metadata or {}
            parts.append(
                f"### {meta.get('runbook_title', 'Untitled')} "
                f"[chunk {meta.get('chunk_index', '?')}] "
                f"(score={match.score:.3f})\n"
                f"{meta.get('text', '')}"
            )
        return "\n\n---\n\n".join(parts)

    except Exception as exc:
        logger.error("search_runbooks failed: %s", exc)
        return f"Error searching runbooks: {exc}"


@tool
def search_incidents(query: str) -> str:
    """Semantic search over past incidents in the incidents Pinecone index.

    Returns the top-3 most similar past incidents with root cause and resolution.
    """
    try:
        vec = embed(query)
        index = _get_pinecone().Index(_INCIDENTS_INDEX)
        results = index.query(vector=vec, top_k=3, include_metadata=True)

        if not results.matches:
            return "No similar past incidents found."

        parts = []
        for i, match in enumerate(results.matches, 1):
            meta = match.metadata or {}
            parts.append(
                f"**Past Incident #{i}** (score={match.score:.3f})\n"
                f"Title: {meta.get('title', 'N/A')}\n"
                f"Root cause: {meta.get('root_cause', 'N/A')}\n"
                f"Resolution: {meta.get('resolution', 'N/A')}\n"
                f"Service: {meta.get('service', 'N/A')}\n"
                f"Duration: {meta.get('duration_minutes', 'N/A')} minutes"
            )
        return "\n\n---\n\n".join(parts)

    except Exception as exc:
        logger.error("search_incidents failed: %s", exc)
        return f"Error searching incidents: {exc}"
