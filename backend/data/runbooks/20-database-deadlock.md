# Runbook: Database Deadlock

**Service Tag:** checkout-service, payment-service, order-service
**Severity Tag:** P2

## Symptoms
- "Deadlock found when trying to get lock" in service logs
- Database error code 1213 (MySQL) or error 40P01 (PostgreSQL)
- Specific transactions failing intermittently
- Retry loops visible in logs

## Diagnostic Steps
1. Check deadlock frequency: `SHOW ENGINE INNODB STATUS;` → look for LATEST DETECTED DEADLOCK
2. Identify tables and rows involved in the deadlock
3. Review transaction isolation level: `SELECT @@tx_isolation;`
4. Correlate deadlock times with recent code deploys
5. Look for N+1 query patterns causing lock contention

## Fix Steps
1. **Short term:** add retry logic with exponential backoff for deadlock errors
2. **Reorder operations** to acquire locks in consistent order
3. **Reduce transaction scope** to hold locks for shorter duration
4. **Add index** if missing index is causing full table locks
5. **Consider lower isolation level** (READ COMMITTED instead of REPEATABLE READ) if safe

## Follow-up Actions
- Add deadlock frequency alert (> 10/min)
- Review transaction ordering in code
- Add database slow query log analysis
- Document lock ordering conventions in team docs
