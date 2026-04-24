# Runbook: Connection Timeout Cascade

**Service Tag:** all-services
**Severity Tag:** P1

## Symptoms
- Cascading failures across multiple services
- Timeouts propagating from one service to its dependents
- High error rates across entire service mesh
- Services that don't directly depend on the failing service also affected

## Diagnostic Steps
1. Build dependency graph: trace errors upstream to source
2. Identify the root failing service using distributed traces
3. Check timeout values across the call chain
4. Look for retry storms amplifying the load

## Fix Steps
1. **Identify and isolate** root failing service
2. **Enable circuit breakers** on failing dependencies to fail fast
3. **Reduce timeouts** on healthy services calling failing ones
4. **Disable retries** temporarily to prevent retry storm amplification
5. **Scale healthy services** that are overwhelmed by retry load

## Follow-up Actions
- Implement circuit breakers across all service-to-service calls
- Add timeout budget / deadline propagation
- Review retry policies (add jitter, limit total retry budget)
- Create failure injection tests to validate circuit breaker behavior
