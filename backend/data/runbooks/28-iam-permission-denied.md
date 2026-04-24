# Runbook: IAM Permission Denied

**Service Tag:** all-services
**Severity Tag:** P2

## Symptoms
- PERMISSION_DENIED errors in service logs
- 403 responses from GCP APIs
- Services unable to access GCP resources they previously could
- Recent IAM policy change or service account rotation

## Diagnostic Steps
1. Check exact error message: note which permission is missing
2. Check service account IAM bindings:
   ```bash
   gcloud projects get-iam-policy <project> --flatten="bindings[].members" \
     --filter="bindings.members:serviceAccount:<sa-email>"
   ```
3. Test permission:
   ```bash
   gcloud auth activate-service-account --key-file=<key.json>
   gcloud <resource> list
   ```
4. Check if Workload Identity is configured correctly
5. Review recent IAM changes in Cloud Audit Logs

## Fix Steps
1. **Grant missing role:**
   ```bash
   gcloud projects add-iam-policy-binding <project> \
     --member="serviceAccount:<sa>" \
     --role="roles/<required-role>"
   ```
2. **Restore revoked role** if accidentally removed
3. **Fix Workload Identity** if KSA-GSA binding is broken

## Follow-up Actions
- Add IAM change alerts via Cloud Audit Log sink
- Document required roles per service in service runbook
- Implement IAM policy as code (Terraform)
- Add least-privilege review to new service checklist
