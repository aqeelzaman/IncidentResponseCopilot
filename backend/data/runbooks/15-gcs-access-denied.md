# Runbook: GCS Bucket Access Denied

**Service Tag:** all-services
**Severity Tag:** P2

## Symptoms
- 403 Forbidden errors when accessing GCS buckets
- "PERMISSION_DENIED" in service logs
- Uploads or reads failing to GCS

## Diagnostic Steps
1. Check service account permissions:
   ```bash
   gcloud projects get-iam-policy <project> --flatten="bindings[].members" --filter="bindings.members:<sa-email>"
   ```
2. Verify bucket-level IAM:
   ```bash
   gsutil iam get gs://<bucket-name>
   ```
3. Check if GOOGLE_APPLICATION_CREDENTIALS is set correctly in the pod
4. Verify Workload Identity binding if using GKE Workload Identity

## Fix Steps
1. **Grant missing role:**
   ```bash
   gsutil iam ch serviceAccount:<sa>@<project>.iam.gserviceaccount.com:roles/storage.objectAdmin gs://<bucket>
   ```
2. **Fix Workload Identity binding:**
   ```bash
   gcloud iam service-accounts add-iam-policy-binding <gsa> \
     --role roles/iam.workloadIdentityUser \
     --member "serviceAccount:<project>.svc.id.goog[<namespace>/<ksa>]"
   ```
3. **Restart pods** to pick up new IAM bindings (may take ~60s to propagate)

## Follow-up Actions
- Document required GCS roles per service
- Add IAM permission validation to deployment pipeline
- Review bucket-level vs project-level IAM grants
