# Runbook: Pod CrashLoopBackOff

**Service Tag:** all-services
**Severity Tag:** P1

## Symptoms
- `kubectl get pods` shows `CrashLoopBackOff`
- Pod restarts incrementing rapidly
- Service partially or fully unavailable

## Diagnostic Steps
1. Describe pod: `kubectl describe pod <pod-name>` — check Events and Exit Code
2. Check previous container logs: `kubectl logs <pod-name> --previous`
3. Exit code meanings: 1=app error, 137=OOMKill, 139=segfault, 143=SIGTERM
4. Check readiness/liveness probe failures
5. Verify ConfigMap / Secret existence: `kubectl get configmap,secret`
6. Check if image exists: `kubectl describe pod | grep Image`

## Fix Steps
1. **OOMKill (exit 137):** see Memory Pressure runbook
2. **App startup error:** check logs for missing env var or bad config
3. **Missing secret/configmap:** create missing resource
4. **Bad image:** roll back to previous tag:
   ```bash
   kubectl rollout undo deployment/<name>
   ```
5. **Probe too aggressive:** adjust probe timing:
   ```yaml
   initialDelaySeconds: 30
   failureThreshold: 5
   ```

## Follow-up Actions
- Add restart count alert (threshold: > 3 restarts in 10 min)
- Improve startup error messages for faster diagnosis
- Add pre-deploy validation for required config keys
