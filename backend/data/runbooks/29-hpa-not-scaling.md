# Runbook: HPA Not Scaling

**Service Tag:** all-services
**Severity Tag:** P2

## Symptoms
- Service under load but HPA not increasing replicas
- CPU/memory above HPA threshold but `kubectl get hpa` shows no scaling
- HPA events show "unable to fetch metrics" or "no recommendation"

## Diagnostic Steps
1. Check HPA status: `kubectl describe hpa <name>`
2. Check metrics server: `kubectl top pods`
3. Verify metrics server is running: `kubectl get pods -n kube-system | grep metrics`
4. Check HPA conditions in describe output
5. Verify min/max replica settings

## Fix Steps
1. **Restart metrics server** if it's down:
   ```bash
   kubectl rollout restart deployment/metrics-server -n kube-system
   ```
2. **Scale manually** as immediate relief:
   ```bash
   kubectl scale deployment/<service> --replicas=20
   ```
3. **Fix HPA metric reference** if wrong metric name
4. **Increase HPA max replicas** if at ceiling:
   ```bash
   kubectl patch hpa <name> -p '{"spec":{"maxReplicas":50}}'
   ```

## Follow-up Actions
- Add HPA scaling event alerting
- Review HPA cooldown periods
- Consider KEDA for more flexible scaling triggers
- Test HPA scaling behavior in staging under load
