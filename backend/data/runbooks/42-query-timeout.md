# Runbook: Database Query Timeout

**Service Tag:** checkout-service, order-service, user-service
**Severity Tag:** P2

## Symptoms
- Queries timing out with "statement timeout" or "query_timeout exceeded"
- Specific endpoints slow or failing
- Database CPU high while query count is normal
- EXPLAIN shows sequential scans on large tables

## Diagnostic Steps
1. Identify timed-out queries in DB logs
2. EXPLAIN ANALYZE the slow query
3. Check for lock contention: `SELECT * FROM pg_locks WHERE granted=false;`
4. Check for table bloat: `SELECT relname, n_dead_tup FROM pg_stat_user_tables ORDER BY n_dead_tup DESC;`
5. Correlate with recent data volume growth

## Fix Steps
1. **Add or fix index** (see missing index runbook)
2. **Kill blocking query:**
   ```sql
   SELECT pg_cancel_backend(pid) FROM pg_stat_activity WHERE wait_event_type = 'Lock';
   ```
3. **VACUUM ANALYZE** to update statistics and reclaim space:
   ```sql
   VACUUM ANALYZE orders;
   ```
4. **Rewrite query** to avoid sequential scan (add LIMIT, reorder joins)
5. **Increase statement timeout** as temporary relief:
   ```sql
   SET statement_timeout = '60s';
   ```

## Follow-up Actions
- Add query timeout monitoring
- Schedule regular VACUUM ANALYZE jobs
- Add query performance regression tests
- Review data retention and archiving strategy for large tables
