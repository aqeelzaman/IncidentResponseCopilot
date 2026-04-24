# Runbook: Latency Spike from Downstream Dependency

**Service Tag:** api-gateway, checkout-service, order-service
**Severity Tag:** P2

## Symptoms
- p99 latency increases significantly (> 2x baseline)
- No increase in CPU or memory on affected service
- Downstream service logs show slow responses or errors
- Traces show time spent in outbound HTTP calls

## Diagnostic Steps
1. Identify which downstream dependency is slow via distributed traces
2. Check downstream service health endpoints
3. Compare latency percentiles across services
4. Check for network issues: `ping`, `traceroute` to downstream host
5. Verify downstream service metrics (CPU, memory, DB latency)
6. Check circuit breaker status if implemented

## Fix Steps
1. **If downstream is unhealthy:** escalate to downstream team
2. **Enable circuit breaker** to fail fast:
   ```python
   # Set circuit breaker threshold in service config
   CIRCUIT_BREAKER_THRESHOLD = 0.5  # 50% error rate triggers open
   ```
3. **Increase timeouts** if downstream is just slow (temporary):
   ```bash
   kubectl set env deployment/<service> DOWNSTREAM_TIMEOUT_MS=10000
   ```
4. **Enable fallback behavior** (cached response / degraded mode)
5. **Scale downstream** if it's under load:
   ```bash
   kubectl scale deployment/<downstream-service> --replicas=10
   ```

## Follow-up Actions
- Implement or tune circuit breaker thresholds
- Add per-dependency latency SLO alerts
- Review timeout values across service mesh
- Add synthetic canary tests for downstream health
