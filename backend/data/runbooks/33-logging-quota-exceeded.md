# Runbook: Cloud Logging Quota Exceeded

**Service Tag:** all-services
**Severity Tag:** P3

## Symptoms
- Log entries being dropped silently
- Monitoring alerts based on logs stop firing (false calm)
- GCP Console shows log exclusions or quota errors

## Diagnostic Steps
1. Check Log ingestion rate in Cloud Console → Logging → Log Explorer
2. Check quota: GCP Console → IAM → Quotas → Cloud Logging
3. Identify top log-generating services via log-based metrics
4. Look for debug logs accidentally enabled in production

## Fix Steps
1. **Disable debug logging immediately** in top-generating service:
   ```bash
   kubectl set env deployment/<service> LOG_LEVEL=INFO
   ```
2. **Add log exclusion filters** for non-critical verbose logs:
   ```bash
   gcloud logging sinks create exclude-debug \
     --log-filter='severity<WARNING AND resource.type="k8s_container"' \
     --destination=logging.googleapis.com/projects/<project>/logs/excluded
   ```
3. **Request quota increase** for legitimate high-volume logging

## Follow-up Actions
- Audit log verbosity in all services
- Add log sampling for high-frequency INFO logs
- Create log-based metrics for critical errors only
- Document log retention and sampling policies
