# Runbook: Cascading Service Failure

**Service Tag:** all-services
**Severity Tag:** P1

## Symptoms
- Multiple services failing simultaneously
- Error propagating upstream through service calls
- Traffic returning 503 across many endpoints
- Single root cause service failing and taking down dependents

## Diagnostic Steps
1. Build real-time dependency map: which services are failing?
2. Check distributed traces for the earliest failure
3. Identify the service with the highest error count
4. Check if a single deployment or config change triggered the cascade
5. Look for retry storms amplifying the problem

## Fix Steps
1. **Isolate the root cause service** by temporarily blocking its traffic
2. **Enable circuit breakers** on all dependencies to stop cascade propagation
3. **Disable retries** across all services temporarily to reduce load
4. **Scale downstream services** to handle retry load
5. **Fix root cause** then gradually re-enable traffic
6. **Roll back** root cause service if it was a bad deploy

## Follow-up Actions
- Implement circuit breakers across entire service mesh
- Add chaos engineering tests for cascade resilience
- Create cascade failure runbook with service dependency map
- Define and test degraded mode for all user-facing services
