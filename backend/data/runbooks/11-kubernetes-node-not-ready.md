# Runbook: Kubernetes Node Not Ready

**Service Tag:** all-services
**Severity Tag:** P1

## Symptoms
- `kubectl get nodes` shows `NotReady` status
- Pods on affected node being evicted
- Node pressure conditions: MemoryPressure, DiskPressure, PIDPressure

## Diagnostic Steps
1. Check node status: `kubectl describe node <node-name>`
2. SSH to node and check kubelet: `systemctl status kubelet`
3. Check node disk/memory: `df -h`, `free -m`
4. Review kubelet logs: `journalctl -u kubelet --since "30 minutes ago"`
5. Check for resource pressure conditions in describe output

## Fix Steps
1. **Restart kubelet:**
   ```bash
   systemctl restart kubelet
   ```
2. **If disk pressure:** clean up unused images:
   ```bash
   docker system prune -f
   crictl rmi --prune
   ```
3. **Cordon and drain** if node needs replacement:
   ```bash
   kubectl cordon <node> && kubectl drain <node> --ignore-daemonsets --delete-emptydir-data
   ```
4. **Recreate node** via node pool rolling update:
   ```bash
   gcloud container clusters upgrade <cluster> --node-pool=<pool> --cluster-version=<version>
   ```

## Follow-up Actions
- Add node NotReady alert with < 2 min response time
- Review node resource requests vs limits ratio
- Enable node auto-repair on GKE node pools
