# Runbook: Pod Eviction Due to Resource Pressure

**Service Tag:** all-services
**Severity Tag:** P1

## Symptoms
- Pods being evicted unexpectedly
- `kubectl describe pod` shows "Evicted" status with reason "The node was low on resource: memory"
- Node memory or disk pressure conditions active

## Diagnostic Steps
1. Check evicted pods: `kubectl get pods --field-selector=status.phase=Failed`
2. Check node pressure: `kubectl describe node <node> | grep -A5 Conditions`
3. Identify which pods are consuming most resources: `kubectl top pods --sort-by=memory`
4. Look for missing resource requests/limits (pods with no limits consume unbounded resources)

## Fix Steps
1. **Add resource requests and limits** to all pods missing them
2. **Set LimitRange** to enforce defaults:
   ```yaml
   apiVersion: v1
   kind: LimitRange
   metadata:
     name: default-limits
   spec:
     limits:
     - default:
         memory: 512Mi
         cpu: 500m
       defaultRequest:
         memory: 256Mi
         cpu: 100m
       type: Container
   ```
3. **Scale up node pool** to reduce pressure:
   ```bash
   gcloud container clusters resize <cluster> --node-pool=<pool> --num-nodes=10
   ```

## Follow-up Actions
- Audit all deployments for missing resource limits
- Enable LimitRange in all namespaces
- Set up resource quota per namespace
- Add node memory pressure alert
