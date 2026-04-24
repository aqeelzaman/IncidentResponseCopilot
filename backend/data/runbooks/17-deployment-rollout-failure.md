# Runbook: Deployment Rollout Failure

**Service Tag:** all-services
**Severity Tag:** P2

## Symptoms
- `kubectl rollout status deployment/<name>` hangs or shows failures
- New pods failing to start while old pods are still running
- `PROGRESSING` condition stuck for > 10 minutes

## Diagnostic Steps
1. Check rollout status: `kubectl rollout status deployment/<name> --timeout=5m`
2. Describe deployment: `kubectl describe deployment <name>`
3. Check new pod events: `kubectl describe pod <new-pod>`
4. Look at new pod logs: `kubectl logs <new-pod>`
5. Check resource quotas: `kubectl describe quota -n <namespace>`

## Fix Steps
1. **Roll back immediately** if new version is broken:
   ```bash
   kubectl rollout undo deployment/<name>
   ```
2. **Check and fix** the underlying issue (bad image, missing config, resource limits)
3. **If resource quota exceeded:** request quota increase or reduce replicas temporarily
4. **Resume stalled rollout** after fix:
   ```bash
   kubectl rollout resume deployment/<name>
   ```

## Follow-up Actions
- Add deployment smoke tests that run post-rollout
- Review Deployment `minReadySeconds` and `progressDeadlineSeconds`
- Implement canary deployments to reduce blast radius
- Add rollout failure alert (stuck > 15 min)
