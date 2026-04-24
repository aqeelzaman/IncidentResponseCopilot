# Runbook: ConfigMap Misconfiguration

**Service Tag:** all-services
**Severity Tag:** P2

## Symptoms
- Service starts but behaves incorrectly
- Wrong feature flags, timeouts, or endpoints in use
- Service logs show unexpected configuration values
- Started after a ConfigMap update

## Diagnostic Steps
1. Check current ConfigMap: `kubectl get configmap <name> -o yaml`
2. Verify pod is using latest ConfigMap (check pod creation time vs ConfigMap update time)
3. Check env vars in pod: `kubectl exec <pod> -- env | grep <KEY>`
4. Compare expected vs actual config values
5. Check if ConfigMap was updated but pod not restarted

## Fix Steps
1. **Roll back ConfigMap:**
   ```bash
   kubectl rollout undo configmap/<name>  # if using GitOps
   # or manually restore previous values
   kubectl edit configmap <name>
   ```
2. **Restart pods** to pick up new ConfigMap:
   ```bash
   kubectl rollout restart deployment/<service>
   ```
3. **If using volume mount:** verify file contents in pod:
   ```bash
   kubectl exec <pod> -- cat /etc/config/<file>
   ```

## Follow-up Actions
- Store ConfigMaps in Git and use GitOps for changes
- Add ConfigMap validation to CI pipeline
- Add config change audit logging
- Test configuration changes in staging before production
