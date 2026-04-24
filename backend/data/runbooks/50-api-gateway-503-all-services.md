# Runbook: API Gateway 503 - All Services Unavailable

**Service Tag:** api-gateway
**Severity Tag:** P1

## Symptoms
- All API endpoints returning 503
- API gateway itself is healthy but backend unreachable
- Load balancer health checks failing for all backends
- Total service outage

## Diagnostic Steps
1. Check if api-gateway pods are running: `kubectl get pods -l app=api-gateway`
2. Check if backend services are running
3. Verify Kubernetes Service endpoints: `kubectl get endpoints`
4. Check network connectivity from api-gateway pods to backend
5. Review recent changes: deployment, ConfigMap, network policy
6. Check if GCP Load Balancer is routing to correct backends

## Fix Steps
1. **Check and fix Kubernetes Services** — ensure selectors match pod labels:
   ```bash
   kubectl describe service <service-name>  # check Endpoints field
   ```
2. **Roll back recent changes:**
   ```bash
   kubectl rollout undo deployment/api-gateway
   ```
3. **Scale up healthy backends:**
   ```bash
   for svc in checkout-service payment-service user-service order-service; do
     kubectl scale deployment/$svc --replicas=10
   done
   ```
4. **Check and fix Network Policies** if they're blocking traffic
5. **Escalate to cloud provider** if VPC/network issue suspected

## Follow-up Actions
- Add end-to-end synthetic monitoring (external probe every 30s)
- Implement multi-region failover for total availability
- Create war room runbook for all-services-down scenario
- Conduct post-incident review within 48 hours
