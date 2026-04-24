# Runbook: Persistent Volume Claim Binding Failure

**Service Tag:** stateful-services, database-pods
**Severity Tag:** P1

## Symptoms
- Pods stuck in `Pending` state
- `kubectl describe pod` shows "waiting for PVC to be bound"
- `kubectl get pvc` shows `Pending` status

## Diagnostic Steps
1. Check PVC status: `kubectl describe pvc <pvc-name>`
2. Check StorageClass: `kubectl get storageclass`
3. Check available PVs: `kubectl get pv`
4. Check if storage quota is exceeded: `kubectl describe quota`
5. Look for provisioner errors in events

## Fix Steps
1. **If StorageClass missing:** create or fix StorageClass
2. **If quota exceeded:** request quota increase or delete unused PVCs
3. **Manually create PV** if dynamic provisioning is unavailable:
   ```yaml
   apiVersion: v1
   kind: PersistentVolume
   spec:
     capacity:
       storage: 50Gi
     storageClassName: standard
     gcePersistentDisk:
       pdName: my-disk
   ```
4. **Check GCP disk quota** in Cloud Console

## Follow-up Actions
- Add PVC binding failure alert
- Review storage quota per namespace
- Document storage class options and use cases
- Add storage capacity planning to capacity review process
