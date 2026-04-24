# Runbook: DB Connection Pool Exhaustion

**Service Tag:** checkout-service, payment-service, order-service
**Severity Tag:** P1

## Symptoms
- Services return 503 or 500 errors
- Log messages: "Connection pool exhausted", "HikariCP connection timed out"
- p99 latency spikes above 2000ms
- `active_connections` metric maxed at `pool_size`
- Downstream DB shows normal CPU / no slow queries

## Diagnostic Steps
1. Check active connection count: `SHOW STATUS LIKE 'Threads_connected';`
2. Query the pool metrics endpoint: `curl http://service:8080/actuator/metrics/hikaricp.connections`
3. Look for long-running transactions: `SELECT * FROM information_schema.processlist WHERE time > 30;`
4. Verify `pool_size` config: `kubectl get configmap db-config -o yaml | grep pool_size`
5. Check if a recent deploy changed connection settings.
6. Inspect connection leak suspects: search logs for `WARNING: A connection was leaked`

## Fix Steps
1. **Immediate (< 5 min):** Increase `pool_size` from 10 → 50 in `db_config` ConfigMap:
   ```bash
   kubectl patch configmap db-config -p '{"data":{"pool_size":"50"}}'
   ```
2. **Restart affected pods** to pick up new config:
   ```bash
   kubectl rollout restart deployment/checkout-service
   ```
3. **Kill long-running transactions** (if identified):
   ```sql
   KILL <process_id>;
   ```
4. **Verify recovery:** watch error rate drop on Grafana dashboard.

## Follow-up Actions
- Add connection pool monitoring alert (threshold: `active_connections / pool_size > 0.85`)
- Review connection leak suspects in code review
- Consider connection pooler (PgBouncer / ProxySQL) for long-term scalability
- Document new `pool_size` value in service runbook

## Related Incidents
- INC-2024-0312: checkout-service DB pool exhaustion (resolved by increasing pool_size)
- INC-2023-1108: payment-service similar issue after traffic spike during Black Friday
