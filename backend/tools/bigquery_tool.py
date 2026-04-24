import logging
import os
from datetime import datetime, timedelta, timezone

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

_BQ_DATASET = os.getenv("BIGQUERY_DATASET", "incident_copilot")
_GCP_PROJECT = os.getenv("GCP_PROJECT_ID", "")

_bq = None


def _get_bq():
    global _bq
    if _bq is None:
        from google.cloud import bigquery  # type: ignore

        _bq = bigquery.Client(project=_GCP_PROJECT)
    return _bq


@tool
def query_logs(service: str, time_window_hours: int = 2) -> str:
    """Query BigQuery service_logs for ERROR/CRITICAL rows in the last N hours.

    Returns the top 20 log messages and a total error count as a formatted string.
    """
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=time_window_hours)).isoformat()
        table = f"`{_GCP_PROJECT}.{_BQ_DATASET}.service_logs`"
        sql = f"""
            SELECT timestamp, severity, message
            FROM {table}
            WHERE service_name = @service
              AND severity IN ('ERROR', 'CRITICAL')
              AND timestamp >= @cutoff
            ORDER BY timestamp DESC
            LIMIT 20
        """
        from google.cloud import bigquery  # type: ignore

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("service", "STRING", service),
                bigquery.ScalarQueryParameter("cutoff", "STRING", cutoff),
            ]
        )
        rows = list(_get_bq().query(sql, job_config=job_config).result())

        count_sql = f"""
            SELECT COUNT(*) as total
            FROM {table}
            WHERE service_name = @service
              AND severity IN ('ERROR', 'CRITICAL')
              AND timestamp >= @cutoff
        """
        count_rows = list(_get_bq().query(count_sql, job_config=job_config).result())
        total = count_rows[0]["total"] if count_rows else 0

        if not rows:
            return f"No ERROR/CRITICAL logs found for service '{service}' in the last {time_window_hours}h."

        lines = [f"Total ERROR/CRITICAL count (last {time_window_hours}h): {total}\n\nTop 20 log messages:"]
        for r in rows:
            lines.append(f"  [{r['timestamp']}] {r['severity']}: {r['message']}")
        return "\n".join(lines)

    except Exception as exc:
        logger.error("query_logs failed: %s", exc)
        return f"Error querying logs: {exc}"


@tool
def query_metrics(service: str, metric: str, time_window_hours: int = 2) -> str:
    """Query BigQuery service_metrics for p50/p95/p99/max of a metric in the last N hours."""
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=time_window_hours)).isoformat()
        table = f"`{_GCP_PROJECT}.{_BQ_DATASET}.service_metrics`"
        sql = f"""
            SELECT
              APPROX_QUANTILES(value, 100)[OFFSET(50)]  AS p50,
              APPROX_QUANTILES(value, 100)[OFFSET(95)]  AS p95,
              APPROX_QUANTILES(value, 100)[OFFSET(99)]  AS p99,
              MAX(value)                                 AS max_val,
              COUNT(*)                                   AS sample_count
            FROM {table}
            WHERE service_name = @service
              AND metric_name  = @metric
              AND timestamp    >= @cutoff
        """
        from google.cloud import bigquery  # type: ignore

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("service", "STRING", service),
                bigquery.ScalarQueryParameter("metric", "STRING", metric),
                bigquery.ScalarQueryParameter("cutoff", "STRING", cutoff),
            ]
        )
        rows = list(_get_bq().query(sql, job_config=job_config).result())

        if not rows or rows[0]["sample_count"] == 0:
            return f"No metric data for '{metric}' on service '{service}' in the last {time_window_hours}h."

        r = rows[0]
        return (
            f"Metric '{metric}' for '{service}' (last {time_window_hours}h, n={r['sample_count']}):\n"
            f"  p50={r['p50']:.2f}  p95={r['p95']:.2f}  p99={r['p99']:.2f}  max={r['max_val']:.2f}"
        )

    except Exception as exc:
        logger.error("query_metrics failed: %s", exc)
        return f"Error querying metrics: {exc}"
