# Runbook: Cloud SQL Connection Issues

**Service Tag:** checkout-service, payment-service, user-service
**Severity Tag:** P1

## Symptoms
- "Connection refused" or "too many connections" to Cloud SQL
- Cloud SQL max_connections limit reached
- Cloud SQL proxy pod errors
- Services cannot reach database

## Diagnostic Steps
1. Check Cloud SQL connections in GCP Console → SQL → Connections
2. Check Cloud SQL proxy logs: `kubectl logs -l app=cloudsql-proxy`
3. Verify max_connections: `SELECT @@max_connections;`
4. Count active connections: `SELECT COUNT(*) FROM information_schema.processlist;`
5. Check Cloud SQL instance metrics for CPU/memory saturation

## Fix Steps
1. **Kill idle connections:**
   ```sql
   SELECT CONCAT('KILL ', id, ';') FROM information_schema.processlist WHERE command='Sleep' AND time > 300;
   ```
2. **Increase max_connections** in Cloud SQL flags (requires restart):
   ```bash
   gcloud sql instances patch <instance> --database-flags=max_connections=500
   ```
3. **Deploy PgBouncer** as connection pooler for long-term fix
4. **Restart Cloud SQL Proxy** pods if they're in bad state:
   ```bash
   kubectl rollout restart deployment/cloudsql-proxy
   ```

## Follow-up Actions
- Implement PgBouncer or pgpool-II as connection pooler
- Add max_connections utilization alert (> 80%)
- Review connection pool settings per application
- Consider Cloud SQL read replicas for read-heavy workloads
