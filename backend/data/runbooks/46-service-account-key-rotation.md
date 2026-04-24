# Runbook: Service Account Key Rotation

**Service Tag:** all-services
**Severity Tag:** P2

## Symptoms
- Authentication failures after key rotation
- "invalid_grant" or "UNAUTHENTICATED" errors
- Services that use JSON key files failing to authenticate

## Diagnostic Steps
1. Check key validity: `gcloud iam service-accounts keys list --iam-account=<sa>`
2. Verify key file is correctly base64-encoded in Kubernetes secret
3. Check if GOOGLE_APPLICATION_CREDENTIALS points to the right path
4. Verify no key expiry (GCP keys don't expire by default, but user-managed may)

## Fix Steps
1. **Create new key:**
   ```bash
   gcloud iam service-accounts keys create new-key.json --iam-account=<sa>
   ```
2. **Update Kubernetes secret:**
   ```bash
   kubectl create secret generic gcp-key --from-file=key.json=new-key.json \
     --dry-run=client -o yaml | kubectl apply -f -
   ```
3. **Restart pods** to pick up new key
4. **Delete old key** after confirming new key works:
   ```bash
   gcloud iam service-accounts keys delete <old-key-id> --iam-account=<sa>
   ```

## Follow-up Actions
- Migrate to Workload Identity to eliminate JSON key files
- Document key rotation schedule
- Add key age monitoring alert (keys > 90 days old)
- Automate rotation with Secret Manager + Cloud Scheduler
