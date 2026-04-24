# Runbook: Secret Rotation Failure

**Service Tag:** all-services
**Severity Tag:** P1

## Symptoms
- Authentication failures after scheduled secret rotation
- "Invalid credentials" or "authentication failed" in service logs
- API keys, DB passwords, or service account keys rejected

## Diagnostic Steps
1. Identify which secret was rotated and when
2. Check if pods have picked up the new secret version
3. Verify Secret Manager version is correct
4. Check if services need restart to reload secrets
5. Confirm old secret version was not prematurely disabled

## Fix Steps
1. **Re-enable old secret version** as emergency rollback:
   ```bash
   gcloud secrets versions enable <version> --secret=<secret-name>
   ```
2. **Restart pods** to pick up new secret:
   ```bash
   kubectl rollout restart deployment/<service>
   ```
3. **Verify secret is mounted correctly:**
   ```bash
   kubectl exec <pod> -- printenv | grep <SECRET_NAME>
   ```
4. **If External Secrets Operator:** force sync:
   ```bash
   kubectl annotate externalsecret <name> force-sync=$(date +%s) --overwrite
   ```

## Follow-up Actions
- Implement blue-green secret rotation (new secret valid before old is disabled)
- Add secret rotation smoke tests
- Document rotation schedule and grace period per secret
- Test rotation procedure in staging first
