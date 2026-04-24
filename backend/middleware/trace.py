import uuid
import logging
from contextvars import ContextVar
from datetime import datetime, timezone

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

# ContextVar so any agent can read the current trace_id without explicit passing
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")


class TraceMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, bq_client=None, bq_dataset: str = "") -> None:
        super().__init__(app)
        self._bq = bq_client
        self._dataset = bq_dataset

    async def dispatch(self, request: Request, call_next):
        tid = request.headers.get("X-Trace-ID") or str(uuid.uuid4())
        token = trace_id_var.set(tid)
        request.state.trace_id = tid

        try:
            response = await call_next(request)
        finally:
            trace_id_var.reset(token)

        response.headers["X-Trace-ID"] = tid
        self._log_to_bigquery(tid, request)
        return response

    def _log_to_bigquery(self, tid: str, request: Request) -> None:
        if self._bq is None:
            return
        try:
            table_ref = f"{self._dataset}.trace_log"
            rows = [
                {
                    "trace_id": tid,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "endpoint": str(request.url.path),
                    "method": request.method,
                    "client_host": request.client.host if request.client else "",
                }
            ]
            errors = self._bq.insert_rows_json(table_ref, rows)
            if errors:
                logger.warning("BigQuery trace_log insert errors: %s", errors)
        except Exception as exc:
            logger.warning("Failed to log trace to BigQuery: %s", exc)
