# Runbook: Memory Pressure and OOM Kills

**Service Tag:** all-services
**Severity Tag:** P1

## Symptoms
- Pods in `OOMKilled` or `CrashLoopBackOff` state
- `kubectl describe pod` shows `OOMKilled` reason
- Memory utilization metric > 90% before restart
- Repeated pod restarts visible in `kubectl get pods`

## Diagnostic Steps
1. Identify OOM'd pods: `kubectl get pods --all-namespaces | grep OOMKilled`
2. Check pod memory limits: `kubectl describe pod <pod-name> | grep -A5 Limits`
3. Review memory utilization trend (last 2h) on Grafana
4. Check for memory leaks: heap dump if JVM service
5. Check if recent code deploy introduced large in-memory structures
6. Look for unbounded caches or session storage

## Fix Steps
1. **Immediate:** Increase memory limit in Deployment spec:
   ```yaml
   resources:
     limits:
       memory: "2Gi"  # increase from current value
     requests:
       memory: "1Gi"
   ```
   Apply: `kubectl apply -f deployment.yaml`
2. **Restart pods** if still in CrashLoopBackOff:
   ```bash
   kubectl rollout restart deployment/<service-name>
   ```
3. **If memory leak suspected:** roll back to previous image:
   ```bash
   kubectl rollout undo deployment/<service-name>
   ```

## Follow-up Actions
- Add memory utilization alert at 85% threshold
- Profile memory usage in staging before next release
- Review heap dump for leak source
- Consider Vertical Pod Autoscaler for automatic right-sizing
