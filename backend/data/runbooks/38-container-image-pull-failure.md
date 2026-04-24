# Runbook: Container Image Pull Failure

**Service Tag:** all-services
**Severity Tag:** P1

## Symptoms
- Pods stuck in `ImagePullBackOff` or `ErrImagePull`
- `kubectl describe pod` shows "Back-off pulling image"
- New deployment failing to start
- Registry authentication error in pod events

## Diagnostic Steps
1. Check exact error: `kubectl describe pod <pod> | grep -A5 "Failed to pull"`
2. Verify image exists: `docker manifest inspect <image>:<tag>`
3. Check if image tag exists in registry
4. Verify pull secret: `kubectl get secret regcred -o yaml`
5. Test registry access from a node

## Fix Steps
1. **If wrong tag:** correct image tag in deployment
2. **If missing pull secret:** create or update:
   ```bash
   kubectl create secret docker-registry regcred \
     --docker-server=gcr.io \
     --docker-username=_json_key \
     --docker-password="$(cat keyfile.json)"
   ```
3. **If GCR:** verify service account has `roles/storage.objectViewer`
4. **Rollback to last working image:**
   ```bash
   kubectl rollout undo deployment/<name>
   ```

## Follow-up Actions
- Add image scan + existence validation to CI before deploy
- Document registry credentials rotation process
- Pin image digests instead of mutable tags
- Add pull failure alert
