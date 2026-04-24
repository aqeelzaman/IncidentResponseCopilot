# Runbook: Database Replication Lag

**Service Tag:** user-service, order-service, reporting-service
**Severity Tag:** P2

## Symptoms
- Read replicas returning stale data
- `SHOW SLAVE STATUS` shows `Seconds_Behind_Master` > 30s
- Reports or analytics returning outdated results
- Application errors due to read-after-write inconsistency

## Diagnostic Steps
1. Check replication lag: `SHOW SLAVE STATUS\G` (look for `Seconds_Behind_Master`)
2. Check for long-running transactions on primary blocking replication
3. Look for parallel replication settings: `SHOW VARIABLES LIKE 'slave_parallel%'`
4. Check replica I/O and SQL thread status
5. Verify replica hardware is not under resource pressure

## Fix Steps
1. **Kill long-running transactions on primary** blocking replication
2. **Enable parallel replication** if not already:
   ```sql
   STOP SLAVE; SET GLOBAL slave_parallel_workers=8;
   SET GLOBAL slave_parallel_type='LOGICAL_CLOCK'; START SLAVE;
   ```
3. **Route reads to primary temporarily** while replica catches up
4. **If replica too far behind:** take a fresh snapshot and reinitialize

## Follow-up Actions
- Add replication lag alert (> 10s warning, > 60s critical)
- Review replica hardware specs vs primary write load
- Consider read replica fleet expansion during peak periods
