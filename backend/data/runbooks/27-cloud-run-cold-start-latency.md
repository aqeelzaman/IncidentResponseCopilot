# Runbook: Cloud Run Cold Start Latency

**Service Tag:** all-services (Cloud Run deployments)
**Severity Tag:** P3

## Symptoms
- Intermittent high latency on first requests after idle period
- p99 latency spikes while p50 is normal
- Latency improves after first few requests (warm instances)
- Cold start visible in Cloud Run request logs

## Diagnostic Steps
1. Check Cloud Run metrics: container startup latency in Cloud Console
2. Check minimum instances setting (0 = cold starts possible)
3. Measure cold start time from Cloud Run logs
4. Identify startup time bottlenecks (heavy dependencies, DB connection init)

## Fix Steps
1. **Set minimum instances** to prevent cold starts:
   ```bash
   gcloud run services update <service> --min-instances=2 --region=us-central1
   ```
2. **Reduce container startup time:**
   - Move heavy initialization to lazy loading
   - Use smaller base images
   - Pre-compile dependencies
3. **Enable CPU always allocated** (keeps CPU during idle):
   ```bash
   gcloud run services update <service> --cpu-boost
   ```

## Follow-up Actions
- Set minimum instances for all P1 services
- Measure and document cold start times per service
- Optimize container image size (use distroless or alpine)
- Add startup latency monitoring
