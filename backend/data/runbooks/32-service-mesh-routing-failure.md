# Runbook: Service Mesh Routing Failure (Istio/Anthos)

**Service Tag:** all-services
**Severity Tag:** P1

## Symptoms
- 503 errors with "no healthy upstream" from Envoy
- Services unreachable despite pods being healthy
- Istio/Envoy sidecar logs show route errors
- VirtualService or DestinationRule misconfiguration after recent change

## Diagnostic Steps
1. Check Envoy proxy config: `istioctl proxy-config routes <pod> --port 80`
2. Verify VirtualService: `kubectl get virtualservice -o yaml`
3. Check DestinationRule: `kubectl get destinationrule -o yaml`
4. Look for Istio control plane issues: `kubectl get pods -n istio-system`
5. Analyze proxy logs: `kubectl logs <pod> -c istio-proxy`

## Fix Steps
1. **Roll back bad VirtualService/DestinationRule:**
   ```bash
   kubectl rollout undo virtualservice/<name>
   # or apply previous known-good config
   ```
2. **Restart istiod** if control plane has issues:
   ```bash
   kubectl rollout restart deployment/istiod -n istio-system
   ```
3. **Restart affected pod sidecars:**
   ```bash
   kubectl rollout restart deployment/<service>
   ```

## Follow-up Actions
- Add Istio config validation to CI pipeline (`istioctl analyze`)
- Add service mesh error rate alerts
- Review DestinationRule subset configurations
- Document service mesh topology
