import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# Lazy BigQuery client — only init if credentials present
_bq_client = None


def _get_bq_client():
    global _bq_client
    if _bq_client is None:
        try:
            from google.cloud import bigquery  # type: ignore

            _bq_client = bigquery.Client(project=os.getenv("GCP_PROJECT_ID"))
        except Exception as exc:
            logger.warning("BigQuery client unavailable: %s", exc)
    return _bq_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Incident Response Copilot backend starting up")
    _get_bq_client()
    yield
    logger.info("Incident Response Copilot backend shutting down")


app = FastAPI(
    title="Incident Response Copilot",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add trace middleware after CORS so trace_id is available to all handlers
from middleware.trace import TraceMiddleware  # noqa: E402

app.add_middleware(
    TraceMiddleware,
    bq_client=None,  # passed lazily below
    bq_dataset=f"{os.getenv('GCP_PROJECT_ID','')}.{os.getenv('BIGQUERY_DATASET','incident_copilot')}",
)


class TriageRequest(BaseModel):
    incident: str


async def _run_triage_stream(incident: str, trace_id: str):
    """Run the LangGraph supervisor and yield SSE-formatted events."""
    from agents.supervisor import build_supervisor_graph

    graph = build_supervisor_graph()
    state = {
        "incident": incident,
        "trace_id": trace_id,
        "log_analysis": "",
        "runbook_match": "",
        "incident_history": "",
        "remediation": "",
        "status": "running",
    }

    agent_order = ["log_analyst", "runbook_rag", "incident_history", "remediation"]
    queue: asyncio.Queue = asyncio.Queue()

    async def _stream_graph():
        try:
            async for chunk in graph.astream(state, config={"configurable": {"trace_id": trace_id}}):
                await queue.put(chunk)
        except Exception as exc:
            logger.error("Graph execution error [trace=%s]: %s", trace_id, exc)
            await queue.put({"__error__": str(exc)})
        finally:
            await queue.put(None)  # sentinel

    asyncio.create_task(_stream_graph())

    while True:
        chunk = await queue.get()
        if chunk is None:
            break
        if "__error__" in chunk:
            yield f"data: {json.dumps({'status': 'error', 'message': chunk['__error__'], 'trace_id': trace_id})}\n\n"
            return

        for node_name, node_output in chunk.items():
            if node_name in agent_order:
                field_map = {
                    "log_analyst": "log_analysis",
                    "runbook_rag": "runbook_match",
                    "incident_history": "incident_history",
                    "remediation": "remediation",
                }
                field = field_map.get(node_name, node_name)
                output_text = node_output.get(field, "") if isinstance(node_output, dict) else str(node_output)
                yield f"data: {json.dumps({'agent': node_name, 'status': 'complete', 'output': output_text})}\n\n"

    yield f"data: {json.dumps({'status': 'done', 'trace_id': trace_id})}\n\n"


@app.post("/api/triage")
async def triage(request: Request, body: TriageRequest):
    trace_id: str = getattr(request.state, "trace_id", "")
    if not body.incident.strip():
        raise HTTPException(status_code=422, detail="incident must not be empty")

    logger.info("Triage request received [trace=%s] incident=%r", trace_id, body.incident[:120])

    return StreamingResponse(
        _run_triage_stream(body.incident, trace_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("BACKEND_PORT", 8000)),
        reload=True,
    )
