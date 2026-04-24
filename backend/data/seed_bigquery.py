"""Seed BigQuery with 6 months of synthetic GCP-style service logs and metrics.

Demo scenario hard-coded:
  checkout-service shows ERROR spike + p99_latency > 2000ms starting
  90 minutes before the current run (matches "started about 90 minutes ago").
"""

import os
import random
import uuid
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from google.cloud import bigquery  # type: ignore

load_dotenv()

PROJECT = os.environ["GCP_PROJECT_ID"]
DATASET = os.getenv("BIGQUERY_DATASET", "incident_copilot")
CLIENT = bigquery.Client(project=PROJECT)
DATASET_REF = f"{PROJECT}.{DATASET}"

SERVICES = [
    "checkout-service",
    "payment-service",
    "inventory-service",
    "auth-service",
    "notification-service",
    "api-gateway",
    "user-service",
    "order-service",
]

NORMAL_MESSAGES = [
    "Request processed successfully",
    "Cache hit ratio: 0.94",
    "DB query completed in 12ms",
    "Health check passed",
    "Outgoing request to downstream service completed",
    "JWT token validated",
    "Queue message processed",
    "Batch job completed",
]

ERROR_MESSAGES_CHECKOUT = [
    "FATAL: Connection pool exhausted — could not acquire connection after 5000ms",
    "ERROR: DB connection timeout after 5000ms (pool_size=10, active=10, waiting=47)",
    "ERROR: Unable to execute query: too many connections to database",
    "ERROR: HikariCP - Connection is not available, request timed out after 30000ms",
    "CRITICAL: checkout transaction failed — database connection refused",
    "ERROR: SQLState[08001] — connection refused by database server",
    "ERROR: Deadlock detected on table 'orders', retrying... attempt 3/3 FAILED",
    "ERROR: p99 latency threshold exceeded: 4247ms > 2000ms SLO",
    "CRITICAL: Pod checkout-service-7d9f4c-xkp2q OOMKilled — restarting",
    "ERROR: Health check failed for database dependency",
]

GENERIC_ERROR_MESSAGES = [
    "ERROR: Upstream timeout",
    "ERROR: Rate limit exceeded",
    "WARN: High memory usage detected",
    "ERROR: Failed to connect to cache",
    "WARN: Slow query detected: 890ms",
]

METRICS = ["p99_latency", "p95_latency", "p50_latency", "error_rate", "cpu_utilization",
           "memory_utilization", "request_rate", "active_connections", "pool_wait_time"]


def create_tables():
    schema_logs = [
        bigquery.SchemaField("timestamp", "TIMESTAMP"),
        bigquery.SchemaField("service_name", "STRING"),
        bigquery.SchemaField("severity", "STRING"),
        bigquery.SchemaField("message", "STRING"),
        bigquery.SchemaField("trace_id", "STRING"),
    ]
    schema_metrics = [
        bigquery.SchemaField("timestamp", "TIMESTAMP"),
        bigquery.SchemaField("service_name", "STRING"),
        bigquery.SchemaField("metric_name", "STRING"),
        bigquery.SchemaField("value", "FLOAT64"),
    ]
    schema_trace = [
        bigquery.SchemaField("trace_id", "STRING"),
        bigquery.SchemaField("timestamp", "TIMESTAMP"),
        bigquery.SchemaField("endpoint", "STRING"),
        bigquery.SchemaField("method", "STRING"),
        bigquery.SchemaField("client_host", "STRING"),
    ]

    dataset = bigquery.Dataset(DATASET_REF)
    dataset.location = "US"
    CLIENT.create_dataset(dataset, exists_ok=True)
    print(f"Dataset {DATASET_REF} ready")

    for table_id, schema in [
        ("service_logs", schema_logs),
        ("service_metrics", schema_metrics),
        ("trace_log", schema_trace),
    ]:
        table = bigquery.Table(f"{DATASET_REF}.{table_id}", schema=schema)
        table.time_partitioning = bigquery.TimePartitioning(field="timestamp")
        CLIENT.create_table(table, exists_ok=True)
        print(f"Table {table_id} ready")


def _ts(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def generate_logs(now: datetime) -> list[dict]:
    rows = []
    start = now - timedelta(days=180)

    for day_offset in range(180):
        day = start + timedelta(days=day_offset)
        for service in SERVICES:
            # ~50 log lines per service per day in normal times
            for _ in range(50):
                ts = day + timedelta(
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59),
                    seconds=random.randint(0, 59),
                )
                severity = random.choices(
                    ["INFO", "INFO", "INFO", "WARN", "ERROR"],
                    weights=[70, 15, 5, 7, 3],
                )[0]
                msg = random.choice(NORMAL_MESSAGES) if severity == "INFO" else random.choice(GENERIC_ERROR_MESSAGES)
                rows.append({
                    "timestamp": _ts(ts),
                    "service_name": service,
                    "severity": severity,
                    "message": msg,
                    "trace_id": str(uuid.uuid4()),
                })

    # Demo scenario: checkout-service error spike starting 90min ago
    spike_start = now - timedelta(minutes=90)
    for i in range(847):  # 847 errors — matches demo scenario
        ts = spike_start + timedelta(seconds=random.randint(0, 5400))  # over 90 min
        rows.append({
            "timestamp": _ts(ts),
            "service_name": "checkout-service",
            "severity": random.choice(["ERROR", "ERROR", "ERROR", "CRITICAL"]),
            "message": random.choice(ERROR_MESSAGES_CHECKOUT),
            "trace_id": str(uuid.uuid4()),
        })

    return rows


def generate_metrics(now: datetime) -> list[dict]:
    rows = []
    start = now - timedelta(days=180)

    for day_offset in range(180):
        day = start + timedelta(days=day_offset)
        for service in SERVICES:
            for metric in METRICS:
                for _ in range(24):  # hourly samples
                    ts = day + timedelta(hours=_ , minutes=random.randint(0, 59))
                    if metric in ("p99_latency", "p95_latency", "p50_latency"):
                        value = random.gauss(120, 30)
                    elif metric == "error_rate":
                        value = random.uniform(0, 0.02)
                    elif metric in ("cpu_utilization", "memory_utilization"):
                        value = random.uniform(20, 60)
                    elif metric == "request_rate":
                        value = random.uniform(50, 300)
                    elif metric == "active_connections":
                        value = random.uniform(2, 8)
                    else:
                        value = random.uniform(0, 100)
                    rows.append({
                        "timestamp": _ts(ts),
                        "service_name": service,
                        "metric_name": metric,
                        "value": max(0.0, value),
                    })

    # Demo scenario: checkout-service metrics spike starting 90min ago
    spike_start = now - timedelta(minutes=90)
    for i in range(90):  # one sample per minute for 90 min
        ts = spike_start + timedelta(minutes=i)
        # p99 latency rockets to 4.2s
        rows.append({"timestamp": _ts(ts), "service_name": "checkout-service",
                     "metric_name": "p99_latency", "value": random.uniform(3800, 4600)})
        rows.append({"timestamp": _ts(ts), "service_name": "checkout-service",
                     "metric_name": "p95_latency", "value": random.uniform(2800, 3600)})
        rows.append({"timestamp": _ts(ts), "service_name": "checkout-service",
                     "metric_name": "error_rate", "value": random.uniform(0.45, 0.65)})
        rows.append({"timestamp": _ts(ts), "service_name": "checkout-service",
                     "metric_name": "active_connections", "value": 10.0})  # maxed out pool
        rows.append({"timestamp": _ts(ts), "service_name": "checkout-service",
                     "metric_name": "pool_wait_time", "value": random.uniform(4500, 5200)})

    return rows


def insert_batch(table_id: str, rows: list[dict], batch_size: int = 1000):
    table_ref = f"{DATASET_REF}.{table_id}"
    total = len(rows)
    for i in range(0, total, batch_size):
        batch = rows[i:i + batch_size]
        errors = CLIENT.insert_rows_json(table_ref, batch)
        if errors:
            print(f"  Insert errors at offset {i}: {errors[:3]}")
        else:
            print(f"  Inserted rows {i}–{min(i+batch_size, total)}/{total}")


def main():
    print("Creating tables...")
    create_tables()

    now = datetime.now(timezone.utc)

    print("Generating log data...")
    logs = generate_logs(now)
    print(f"  Generated {len(logs)} log rows")
    print("Inserting logs...")
    insert_batch("service_logs", logs)

    print("Generating metrics data...")
    metrics = generate_metrics(now)
    print(f"  Generated {len(metrics)} metric rows")
    print("Inserting metrics...")
    insert_batch("service_metrics", metrics)

    print("Done! Demo scenario seeded:")
    print("  checkout-service: 847 ERRORs + p99=4.2s starting 90min ago")


if __name__ == "__main__":
    main()
