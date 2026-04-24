# Runbook: Thread Pool Exhaustion

**Service Tag:** checkout-service, payment-service
**Severity Tag:** P1

## Symptoms
- Requests queuing instead of being processed
- "Thread pool exhausted" or "rejected execution" in logs
- p99 latency grows while p50 remains normal
- Active thread count maxed at thread pool size

## Diagnostic Steps
1. Check active threads: `curl http://service:8080/actuator/metrics/executor.active`
2. Check queue depth: look for `executor.queued` metric
3. Identify which endpoints are consuming threads (thread dump)
4. Look for blocked threads (waiting on I/O, DB, downstream calls)
5. Check if thread pool size changed in recent deploy

## Fix Steps
1. **Increase thread pool size** (temporary):
   ```bash
   kubectl set env deployment/<service> SERVER_TOMCAT_THREADS_MAX=400
   ```
2. **If threads blocked on DB:** address DB connection pool issue first
3. **Add async/non-blocking I/O** for high-latency operations
4. **Reduce downstream timeout** so threads free up faster

## Follow-up Actions
- Add thread pool utilization alert (> 85%)
- Review use of synchronous I/O in high-throughput paths
- Consider reactive/non-blocking framework for I/O-bound services
- Profile thread usage patterns
