"""Seed Pinecone with runbook chunks and synthetic past incidents.

Runbooks index:   chunk_size=512 tokens, overlap=64, metadata includes
                  runbook_title, chunk_index, service_tag, severity_tag, text.
Incidents index:  30 synthetic past incidents embedded by description field.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec  # type: ignore

load_dotenv()

RUNBOOKS_INDEX = os.getenv("PINECONE_RUNBOOKS_INDEX", "runbooks")
INCIDENTS_INDEX = os.getenv("PINECONE_INCIDENTS_INDEX", "incidents")
RUNBOOKS_DIR = Path(__file__).parent / "runbooks"
EMBED_MODEL = "all-MiniLM-L6-v2"
EMBED_DIM = 384  # all-MiniLM-L6-v2 output dimension

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])

from sentence_transformers import SentenceTransformer  # noqa: E402

_st_model = SentenceTransformer(EMBED_MODEL)


def embed(texts: list[str]) -> list[list[float]]:
    return _st_model.encode(texts, normalize_embeddings=True, batch_size=32).tolist()


def ensure_index(name: str, dim: int = EMBED_DIM):
    existing = [idx.name for idx in pc.list_indexes()]
    if name not in existing:
        pc.create_index(
            name=name,
            dimension=dim,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        print(f"Created index: {name}")
    else:
        print(f"Index already exists: {name}")
    return pc.Index(name)


# ─── Runbook chunking ─────────────────────────────────────────────────────────

def _extract_frontmatter(content: str) -> tuple[str, str, str, str]:
    """Extract title, service_tag, severity_tag from markdown header."""
    lines = content.splitlines()
    title = ""
    service_tag = ""
    severity_tag = ""
    for line in lines:
        if line.startswith("# Runbook:"):
            title = line.replace("# Runbook:", "").strip()
        elif line.startswith("**Service Tag:**"):
            service_tag = line.replace("**Service Tag:**", "").strip()
        elif line.startswith("**Severity Tag:**"):
            severity_tag = line.replace("**Severity Tag:**", "").strip()
    return title, service_tag, severity_tag, content


def _chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> list[str]:
    """Simple word-boundary chunking."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def seed_runbooks():
    index = ensure_index(RUNBOOKS_INDEX)
    md_files = sorted(RUNBOOKS_DIR.glob("*.md"))
    print(f"Found {len(md_files)} runbook files")

    vectors = []
    for md_file in md_files:
        content = md_file.read_text()
        title, service_tag, severity_tag, full_text = _extract_frontmatter(content)
        chunks = _chunk_text(full_text)

        texts_to_embed = chunks
        embeddings = embed(texts_to_embed)

        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            vectors.append({
                "id": f"{md_file.stem}-chunk-{i}",
                "values": emb,
                "metadata": {
                    "runbook_title": title,
                    "chunk_index": i,
                    "service_tag": service_tag.split(",")[0].strip(),
                    "severity_tag": severity_tag,
                    "source_file": md_file.name,
                    "text": chunk[:2000],  # Pinecone metadata limit
                },
            })

        print(f"  {md_file.name}: {len(chunks)} chunks")

    # Upsert in batches of 100
    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        index.upsert(vectors=vectors[i:i + batch_size])
        print(f"  Upserted vectors {i}–{min(i+batch_size, len(vectors))}/{len(vectors)}")

    print(f"Runbooks seeded: {len(vectors)} total vectors")


# ─── Synthetic past incidents ─────────────────────────────────────────────────

PAST_INCIDENTS = [
    {
        "id": "INC-2024-0312",
        "title": "checkout-service 503 errors — DB connection pool exhausted",
        "description": "checkout-service returned 503 for 45 minutes. Root cause was DB connection pool exhausted after traffic spike. All 10 connections consumed by slow queries.",
        "root_cause": "Database connection pool exhausted (pool_size=10, insufficient for peak traffic). Slow queries held connections for >30s.",
        "resolution": "Increased pool_size from 10 to 50 in db_config ConfigMap. Restarted checkout-service deployment. Killed long-running queries.",
        "service": "checkout-service",
        "duration_minutes": 45,
        "severity": "P1",
    },
    {
        "id": "INC-2023-1108",
        "title": "payment-service DB pool exhaustion — Black Friday traffic spike",
        "description": "payment-service experienced DB connection pool exhaustion during Black Friday traffic. 6x normal traffic with pool_size unchanged at 10.",
        "root_cause": "DB connection pool (pool_size=10) insufficient for 6x holiday traffic. No auto-scaling of pool configured.",
        "resolution": "Increased pool_size to 100. Added PgBouncer as connection pooler. Pre-scaled replicas before next event.",
        "service": "payment-service",
        "duration_minutes": 62,
        "severity": "P1",
    },
    {
        "id": "INC-2024-0215",
        "title": "checkout-service high latency — missing DB index after schema migration",
        "description": "checkout-service p99 latency grew to 8s after a schema migration dropped and recreated the orders table index.",
        "root_cause": "Index on orders.user_id was missing after schema migration. Full table scans on each checkout request.",
        "resolution": "Added index CONCURRENTLY on orders(user_id). Latency returned to normal within 5 minutes.",
        "service": "checkout-service",
        "duration_minutes": 25,
        "severity": "P2",
    },
    {
        "id": "INC-2024-0118",
        "title": "auth-service token expiry cascade — all services 401",
        "description": "All services returned 401 simultaneously as JWT tokens expired at the same time. Token refresh storm overwhelmed auth-service.",
        "root_cause": "All JWT tokens were issued within a 5-minute window during last deployment, causing synchronized expiry.",
        "resolution": "Added token expiry jitter (±30 min). Scaled auth-service to 20 replicas during recovery. Re-issued all tokens.",
        "service": "auth-service",
        "duration_minutes": 30,
        "severity": "P1",
    },
    {
        "id": "INC-2024-0402",
        "title": "order-service OOM kills — memory leak after v2.3 deploy",
        "description": "order-service pods repeatedly OOMKilled after deploying v2.3. Memory grew from 512MB to 2GB over 4 hours.",
        "root_cause": "Memory leak in event listener registration — listeners added on each request but never removed.",
        "resolution": "Rolled back to v2.2. Fixed listener deregistration in v2.3.1. Added memory growth rate alert.",
        "service": "order-service",
        "duration_minutes": 240,
        "severity": "P2",
    },
    {
        "id": "INC-2024-0520",
        "title": "api-gateway 503 — load balancer health check firewall block",
        "description": "api-gateway returned 503 to all external traffic. Load balancer health checks failing due to missing firewall rule for health check probe IPs.",
        "root_cause": "Terraform apply removed firewall rule allowing GCP health check probe IPs (35.191.0.0/16) to reach api-gateway.",
        "resolution": "Re-added firewall rule. Traffic restored within 2 minutes. Terraform state corrected.",
        "service": "api-gateway",
        "duration_minutes": 18,
        "severity": "P1",
    },
    {
        "id": "INC-2024-0601",
        "title": "checkout-service DB connection pool — post-deploy pool_size regression",
        "description": "checkout-service pool_size accidentally reverted to 5 after ConfigMap merge conflict resolved incorrectly.",
        "root_cause": "Git merge conflict in db_config.yaml resolved incorrectly, reverting pool_size from 50 to 5.",
        "resolution": "Fixed ConfigMap pool_size to 50. Restarted deployment. Added pool_size validation to deployment pipeline.",
        "service": "checkout-service",
        "duration_minutes": 15,
        "severity": "P1",
    },
    {
        "id": "INC-2024-0703",
        "title": "user-service replication lag — replica returning stale data",
        "description": "user-service read replicas lagged 5+ minutes behind primary after a large batch import job.",
        "root_cause": "Batch import created high primary write load. Replication lag exceeded 5 minutes causing stale reads.",
        "resolution": "Routed all reads to primary temporarily. Enabled parallel replication. Lag resolved in 20 minutes.",
        "service": "user-service",
        "duration_minutes": 35,
        "severity": "P2",
    },
    {
        "id": "INC-2024-0808",
        "title": "notification-service Pub/Sub backlog — consumer crash loop",
        "description": "notification-service consumers crashed due to malformed message, causing DLQ to fill and backlog to grow to 500k messages.",
        "root_cause": "Schema change in producer broke notification-service consumer. Consumers crash-looped on malformed messages.",
        "resolution": "Fixed consumer schema handling. Added DLQ processing. Replayed backlog over 2 hours.",
        "service": "notification-service",
        "duration_minutes": 120,
        "severity": "P2",
    },
    {
        "id": "INC-2024-0912",
        "title": "payment-service cascading timeout from DB slowdown",
        "description": "payment-service requests timed out due to slow DB queries. Thread pool exhausted holding threads waiting for DB.",
        "root_cause": "Missing index on payments.order_id caused full table scans, slowing queries from 10ms to 8000ms.",
        "resolution": "Added index on payments(order_id). Increased thread pool size temporarily. Queries returned to 10ms.",
        "service": "payment-service",
        "duration_minutes": 40,
        "severity": "P1",
    },
    {
        "id": "INC-2024-1005",
        "title": "inventory-service negative stock counts",
        "description": "Inventory service showed negative stock counts for popular items. Orders placed for out-of-stock items.",
        "root_cause": "Race condition in inventory decrement — missing optimistic lock allowed double-decrement.",
        "resolution": "Added optimistic locking with version field. Reconciled inventory from order history. Added negative stock alert.",
        "service": "inventory-service",
        "duration_minutes": 90,
        "severity": "P2",
    },
    {
        "id": "INC-2024-1101",
        "title": "checkout-service high error rate — Redis cache stampede",
        "description": "checkout-service experienced 503 errors when product cache expired simultaneously, overwhelming DB.",
        "root_cause": "All product cache keys expired simultaneously (same TTL set for all). DB overwhelmed by 10x normal query rate.",
        "resolution": "Added TTL jitter (±10% random variance). Pre-warmed cache. Error rate recovered in 5 minutes.",
        "service": "checkout-service",
        "duration_minutes": 8,
        "severity": "P2",
    },
    {
        "id": "INC-2024-1115",
        "title": "order-service circuit breaker opened — payment-service slow",
        "description": "order-service circuit breaker opened for payment-service after payment latency exceeded 5s for >50% of calls.",
        "root_cause": "Payment provider Stripe experienced degraded performance. Circuit breaker correctly opened to protect order-service.",
        "resolution": "Monitored Stripe status page. Circuit breaker auto-recovered after Stripe resolved issue. No code changes needed.",
        "service": "order-service",
        "duration_minutes": 55,
        "severity": "P2",
    },
    {
        "id": "INC-2024-1201",
        "title": "api-gateway certificate expiry — all HTTPS connections failing",
        "description": "API gateway TLS certificate expired. All HTTPS connections failed. cert-manager renewal had silently failed 30 days prior.",
        "root_cause": "cert-manager failed to renew certificate (DNS challenge failed). No alert on renewal failure.",
        "resolution": "Manually renewed certificate. Fixed DNS challenge configuration. Added cert expiry alert.",
        "service": "api-gateway",
        "duration_minutes": 22,
        "severity": "P1",
    },
    {
        "id": "INC-2023-0615",
        "title": "checkout-service DB pool exhaustion — slow query from missing index",
        "description": "checkout-service connections exhausted as slow queries (8s+) held connections. Root cause: index dropped during migration.",
        "root_cause": "DB connection pool exhausted. Underlying cause: slow query (full table scan) holding connections for 8s due to missing index.",
        "resolution": "Killed slow queries. Added index. Increased pool_size to 50 as safety margin.",
        "service": "checkout-service",
        "duration_minutes": 28,
        "severity": "P1",
    },
    {
        "id": "INC-2023-0820",
        "title": "checkout-service 503 — pool_size too small after traffic ramp",
        "description": "New marketing campaign drove 3x traffic to checkout. DB connection pool (pool_size=10) exhausted within minutes.",
        "root_cause": "DB connection pool too small for 3x traffic increase. pool_size=10 insufficient.",
        "resolution": "Emergency pool_size increase to 50. Deployed PgBouncer. Traffic normalized after 35 minutes.",
        "service": "checkout-service",
        "duration_minutes": 35,
        "severity": "P1",
    },
    {
        "id": "INC-2023-1210",
        "title": "Node NotReady — disk pressure after log accumulation",
        "description": "Three GKE nodes went NotReady due to disk pressure from accumulated container logs filling root disk.",
        "root_cause": "Container logs not rotated. Root disk 100% full triggering node disk pressure condition.",
        "resolution": "Cleaned up logs. Added logrotate configuration. Cordoned and drained affected nodes.",
        "service": "all-services",
        "duration_minutes": 45,
        "severity": "P1",
    },
    {
        "id": "INC-2023-0905",
        "title": "DNS resolution failures — CoreDNS OOM",
        "description": "Services unable to resolve each other by hostname. CoreDNS pods OOMKilled due to DNS cache unbounded growth.",
        "root_cause": "CoreDNS memory not limited. DNS cache grew unbounded to 2GB, triggering OOMKill.",
        "resolution": "Set CoreDNS memory limit 512Mi. Enabled DNS caching limits. Added CoreDNS memory alert.",
        "service": "all-services",
        "duration_minutes": 20,
        "severity": "P1",
    },
    {
        "id": "INC-2023-1025",
        "title": "IAM permission denied — Workload Identity misconfiguration",
        "description": "Services unable to access Cloud SQL after Workload Identity binding was accidentally deleted during Terraform apply.",
        "root_cause": "Terraform plan incorrectly showed Workload Identity binding as unchanged, but apply deleted it.",
        "resolution": "Restored Workload Identity binding. Services recovered after pod restart. Terraform state corrected.",
        "service": "all-services",
        "duration_minutes": 30,
        "severity": "P1",
    },
    {
        "id": "INC-2024-0110",
        "title": "HPA not scaling — metrics-server pod failure",
        "description": "checkout-service under heavy load but HPA stuck at minimum replicas. metrics-server pod had crashed.",
        "root_cause": "metrics-server pod in CrashLoopBackOff due to node resource pressure. HPA unable to fetch metrics.",
        "resolution": "Restarted metrics-server. Manually scaled checkout-service. Fixed node resource pressure.",
        "service": "checkout-service",
        "duration_minutes": 25,
        "severity": "P2",
    },
    {
        "id": "INC-2024-0225",
        "title": "Thread pool exhaustion — checkout-service blocking on slow DB",
        "description": "checkout-service thread pool exhausted. All threads blocked waiting for DB connections that were themselves exhausted.",
        "root_cause": "Thread pool and DB connection pool both exhausted simultaneously. DB slowdown caused threads to block, filling thread pool.",
        "resolution": "Increased both thread pool (200→400) and DB connection pool (10→50). Killed slow DB queries.",
        "service": "checkout-service",
        "duration_minutes": 35,
        "severity": "P1",
    },
    {
        "id": "INC-2024-0317",
        "title": "Cascading failure — payment-service DB timeout caused order-service cascade",
        "description": "payment-service DB timeout caused payment-service to become slow. order-service threads blocked on payment calls. api-gateway queued up.",
        "root_cause": "Cascade: DB index missing → payment-service slow → order-service thread pool exhausted → api-gateway queue full.",
        "resolution": "Added DB index. Enabled circuit breaker on payment-service dependency. Scaled all services.",
        "service": "payment-service",
        "duration_minutes": 55,
        "severity": "P1",
    },
    {
        "id": "INC-2024-0430",
        "title": "BigQuery quota exceeded — runaway analytics query",
        "description": "Analytics service query without LIMIT clause scanned entire 2-year dataset repeatedly, exhausting daily quota.",
        "root_cause": "New analytics query missing WHERE clause processed 4TB instead of 40MB. Daily quota exhausted in 3 hours.",
        "resolution": "Killed runaway queries. Added maximumBytesBilled limit. Added WHERE clause to query.",
        "service": "analytics-service",
        "duration_minutes": 180,
        "severity": "P2",
    },
    {
        "id": "INC-2024-0514",
        "title": "Cloud Run cold starts — checkout-service latency spikes on 0 instances",
        "description": "checkout-service min-instances=0. After 20-minute traffic lull, cold starts added 8s to first requests.",
        "root_cause": "Cloud Run scaled to 0 instances during low traffic. Heavy dependency initialization on cold start.",
        "resolution": "Set min-instances=3 for checkout-service. Optimized startup time from 8s to 2s.",
        "service": "checkout-service",
        "duration_minutes": 15,
        "severity": "P3",
    },
    {
        "id": "INC-2024-0622",
        "title": "Secret rotation broke payment-service",
        "description": "payment-service authentication to payment provider failed after API key rotation. Old key deactivated before new key distributed.",
        "root_cause": "Secret rotation race: old API key deactivated at 14:00, new Kubernetes secret not applied until 14:15.",
        "resolution": "Re-enabled old key temporarily. Applied new secret. Restarted payment-service. Implemented zero-downtime rotation.",
        "service": "payment-service",
        "duration_minutes": 15,
        "severity": "P1",
    },
    {
        "id": "INC-2024-0715",
        "title": "Kafka consumer lag — notification-service CPU throttling",
        "description": "Notification consumer lag grew to 200k messages. Root cause: CPU limits too low causing notification-service to process only 10% capacity.",
        "root_cause": "notification-service CPU limit 100m (0.1 core) was 10x too low for message processing throughput.",
        "resolution": "Increased CPU limit to 1000m. Consumer lag cleared in 45 minutes.",
        "service": "notification-service",
        "duration_minutes": 90,
        "severity": "P2",
    },
    {
        "id": "INC-2024-0822",
        "title": "Firestore hot document — order counter contention",
        "description": "order-service write latency spiked due to hot order counter document being updated by all service instances.",
        "root_cause": "Single Firestore document used as order ID counter, receiving >100 writes/second (limit: 1/second).",
        "resolution": "Replaced single counter with 100-shard distributed counter. Write latency normalized.",
        "service": "order-service",
        "duration_minutes": 60,
        "severity": "P2",
    },
    {
        "id": "INC-2024-0930",
        "title": "GKE node disk pressure — logs not rotated",
        "description": "Multiple GKE nodes hit disk pressure condition. Pods evicted. Root cause: container log files not rotated, filling 100GB disk.",
        "root_cause": "Container runtime log rotation not configured. Long-running pods accumulated 80GB+ of logs.",
        "resolution": "Configured container log rotation (maxSize: 100Mi, maxFiles: 5). Cleaned existing logs. Added disk alert.",
        "service": "all-services",
        "duration_minutes": 50,
        "severity": "P1",
    },
    {
        "id": "INC-2024-1015",
        "title": "VPC firewall rule blocked Cloud SQL proxy",
        "description": "Terraform apply inadvertently deleted firewall rule allowing GKE pods to reach Cloud SQL proxy. All DB-backed services failed.",
        "root_cause": "Terraform drift — firewall rule created manually (not in state) was deleted on apply.",
        "resolution": "Re-added firewall rule via gcloud. All services recovered. Added rule to Terraform.",
        "service": "all-services",
        "duration_minutes": 12,
        "severity": "P1",
    },
    {
        "id": "INC-2024-1110",
        "title": "Deployment rollout stuck — new image OOMKilled immediately",
        "description": "checkout-service deployment rollout stuck. New pods OOMKilled on startup. Memory limit 128Mi insufficient for new version (requires 256Mi).",
        "root_cause": "New version dependency added 150MB to memory footprint. Existing 128Mi limit insufficient.",
        "resolution": "Rolled back deployment. Increased memory limit to 512Mi. Redeployed successfully.",
        "service": "checkout-service",
        "duration_minutes": 20,
        "severity": "P2",
    },
]


def seed_incidents():
    index = ensure_index(INCIDENTS_INDEX)
    texts = [inc["description"] for inc in PAST_INCIDENTS]
    embeddings = embed(texts)

    vectors = []
    for inc, emb in zip(PAST_INCIDENTS, embeddings):
        vectors.append({
            "id": inc["id"],
            "values": emb,
            "metadata": {
                "title": inc["title"],
                "description": inc["description"][:2000],
                "root_cause": inc["root_cause"],
                "resolution": inc["resolution"],
                "service": inc["service"],
                "duration_minutes": inc["duration_minutes"],
                "severity": inc["severity"],
            },
        })

    index.upsert(vectors=vectors)
    print(f"Incidents seeded: {len(vectors)} past incidents")


def main():
    print("=== Seeding Runbooks ===")
    seed_runbooks()
    print("\n=== Seeding Past Incidents ===")
    seed_incidents()
    print("\nDone!")


if __name__ == "__main__":
    main()
