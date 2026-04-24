# Runbook: Load Balancer Health Check Failures

**Service Tag:** api-gateway, all-services
**Severity Tag:** P1

## Symptoms
- GCP Load Balancer reports unhealthy backends
- Traffic not reaching service despite pods being Running
- Health check endpoint returning non-2xx or timing out
- Users receiving 502/503 from load balancer

## Diagnostic Steps
1. Check backend health in GCP Console → Load Balancing
2. Manually curl health endpoint from a pod in same network
3. Check if health endpoint requires authentication (misconfiguration)
4. Verify health check port matches service port
5. Check firewall rules allow health check probe IPs (35.191.0.0/16, 130.211.0.0/22)

## Fix Steps
1. **Fix firewall rule** to allow health check probes:
   ```bash
   gcloud compute firewall-rules create allow-health-check \
     --allow tcp:<port> \
     --source-ranges 35.191.0.0/16,130.211.0.0/22
   ```
2. **Fix health endpoint** to return 200 without auth
3. **Adjust health check thresholds** if service is slow to start:
   - Healthy threshold: 2
   - Unhealthy threshold: 3
   - Check interval: 10s

## Follow-up Actions
- Add health check endpoint tests to CI pipeline
- Document all health check endpoint requirements
- Review firewall rules annually
