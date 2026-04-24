# Runbook: Disk I/O Saturation

**Service Tag:** all-services
**Severity Tag:** P2

## Symptoms
- High disk I/O wait in `top` / `iostat`
- Slow log writes, database query slowdowns
- `io_wait` metric > 50%
- Application latency spikes without CPU increase

## Diagnostic Steps
1. Check I/O stats: `iostat -x 1 10`
2. Identify top I/O consumers: `iotop -o`
3. Check disk utilization: `df -h`
4. Look for runaway log writers or large batch jobs
5. Check database WAL / redo log write rates

## Fix Steps
1. **Kill runaway process** if identified via `iotop`
2. **Move logs to a separate volume** if log writes are saturating
3. **Increase PVC size** if disk is full:
   ```bash
   kubectl patch pvc <pvc-name> -p '{"spec":{"resources":{"requests":{"storage":"100Gi"}}}}'
   ```
4. **Enable log rotation** to cap disk usage
5. **Migrate to SSD-backed storage class** for latency-sensitive workloads

## Follow-up Actions
- Add disk I/O utilization alert (threshold: 80%)
- Add disk space alert (threshold: 85% full)
- Review log retention policies
- Consider moving write-heavy workloads to dedicated nodes
