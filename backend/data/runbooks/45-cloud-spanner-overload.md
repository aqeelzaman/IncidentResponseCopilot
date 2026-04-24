# Runbook: Cloud Spanner Instance Overload

**Service Tag:** global-data-service, inventory-service
**Severity Tag:** P1

## Symptoms
- Spanner CPU utilization > 65% sustained (recommended max for HA)
- Increased query latency across all Spanner-backed services
- Read/write throughput below expected levels
- Spanner metrics show high transaction abort rate

## Diagnostic Steps
1. Check CPU utilization in GCP Console → Cloud Spanner → Monitoring
2. Identify top-consuming queries via Spanner Query Stats
3. Check if recent schema change or traffic spike triggered the issue
4. Review transaction abort rate — high aborts indicate lock contention

## Fix Steps
1. **Add processing units (scale up):**
   ```bash
   gcloud spanner instances update <instance> --processing-units=3000
   ```
2. **Optimize hot queries** identified in Query Stats
3. **Reduce transaction size** — batch large operations
4. **Use stale reads** for read-heavy workloads that tolerate eventual consistency:
   ```python
   with db.snapshot(exact_staleness=datetime.timedelta(seconds=10)) as snapshot:
       results = snapshot.execute_sql(query)
   ```

## Follow-up Actions
- Add Spanner CPU alert (> 65%)
- Review query performance with SPANNER_SYS.QUERY_STATS_TOP_HOUR
- Implement schema design review for hotspot prevention
- Document scaling runbook with processing unit tiers
