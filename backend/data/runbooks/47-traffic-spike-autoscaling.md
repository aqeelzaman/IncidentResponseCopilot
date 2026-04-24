# Runbook: Unexpected Traffic Spike and Autoscaling

**Service Tag:** api-gateway, checkout-service
**Severity Tag:** P2

## Symptoms
- Sudden 2-10x traffic increase
- HPA scaling but lagging behind demand
- Increased error rate during scaling period
- Request queuing visible in latency percentiles

## Diagnostic Steps
1. Identify traffic source: `kubectl logs -l app=api-gateway | grep -c "POST /api/checkout"`
2. Check if traffic is legitimate (marketing campaign, news event, attack)
3. Monitor scaling events: `kubectl get events --sort-by='.lastTimestamp'`
4. Check HPA status and scaling velocity
5. Review which endpoints are being hit

## Fix Steps
1. **Pre-scale immediately** (don't wait for HPA):
   ```bash
   kubectl scale deployment/checkout-service --replicas=50
   kubectl scale deployment/api-gateway --replicas=30
   ```
2. **Enable traffic shedding** on rate limiter if attack
3. **Reduce response size** to serve more requests per second
4. **Cache aggressively** for read-heavy surge traffic
5. **Enable Cloud CDN** if static or cacheable content is the bottleneck

## Follow-up Actions
- Implement predictive scaling for known traffic events
- Review HPA scaling speed (scale-up stabilization window)
- Add load testing to deployment pipeline
- Create traffic surge playbook for marketing/sales events
