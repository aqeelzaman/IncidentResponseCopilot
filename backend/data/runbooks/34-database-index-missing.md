# Runbook: Missing Database Index Causing Slow Queries

**Service Tag:** checkout-service, order-service, user-service
**Severity Tag:** P2

## Symptoms
- Specific queries suddenly much slower after data growth or schema change
- Database CPU spike despite low query volume
- Slow query log shows full table scans
- Service latency grows proportionally to table size

## Diagnostic Steps
1. Enable slow query log: `SET GLOBAL slow_query_log=1; SET GLOBAL long_query_time=0.1;`
2. Identify slow queries: `SELECT * FROM mysql.slow_log ORDER BY query_time DESC LIMIT 10;`
3. EXPLAIN the slow query: `EXPLAIN SELECT * FROM orders WHERE user_id=?;`
4. Look for "ALL" in type column (full table scan) or high rows value

## Fix Steps
1. **Add missing index** (use CONCURRENTLY in PostgreSQL to avoid lock):
   ```sql
   -- PostgreSQL:
   CREATE INDEX CONCURRENTLY idx_orders_user_id ON orders(user_id);
   -- MySQL:
   ALTER TABLE orders ADD INDEX idx_user_id (user_id), ALGORITHM=INPLACE, LOCK=NONE;
   ```
2. **Verify index is used:** re-run EXPLAIN after adding index
3. **Consider composite index** if multiple columns filtered frequently

## Follow-up Actions
- Add slow query monitoring alert (> 1s query time)
- Run `pt-index-usage` to find unused indexes
- Add index creation to deployment checklist for schema changes
- Review query plans before major traffic events
