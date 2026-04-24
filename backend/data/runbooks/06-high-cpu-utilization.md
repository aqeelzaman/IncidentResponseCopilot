# Runbook: High CPU Utilization

**Service Tag:** all-services
**Severity Tag:** P2

## Symptoms
- CPU utilization > 85% sustained for > 5 minutes
- Service latency increases proportionally
- HPA may be scaling but lagging behind demand
- Thread pool exhaustion in high-CPU scenarios

## Diagnostic Steps
1. Identify which pods are CPU-bound: `kubectl top pods`
2. Profile CPU usage: thread dump, flame graph if possible
3. Check for infinite loops or regex catastrophic backtracking in logs
4. Verify if traffic spike is the root cause
5. Check recent deploys for CPU-intensive code paths

## Fix Steps
1. **Scale out immediately:**
   ```bash
   kubectl scale deployment/<service> --replicas=20
   ```
2. **Increase HPA max replicas** if hitting ceiling:
   ```bash
   kubectl patch hpa <service>-hpa -p '{"spec":{"maxReplicas":30}}'
   ```
3. **If specific request type is CPU-heavy:** add rate limiting for that endpoint
4. **Roll back** if recent deploy introduced regression:
   ```bash
   kubectl rollout undo deployment/<service>
   ```

## Follow-up Actions
- Tune HPA target CPU threshold (consider lowering from 80% to 60%)
- Profile and optimize hot code paths
- Add CPU profiling to CI pipeline for performance regressions
- Review rate limiting configuration
