# Runbook: DNS Resolution Failures

**Service Tag:** all-services
**Severity Tag:** P1

## Symptoms
- Services unable to reach each other by hostname
- "Unknown host" or "Name or service not known" errors
- kube-dns or CoreDNS pod showing errors/restarts
- Latency spikes at connection establishment (not in request processing)

## Diagnostic Steps
1. Test DNS from a pod: `kubectl exec -it <pod> -- nslookup <service-name>`
2. Check CoreDNS status: `kubectl get pods -n kube-system -l k8s-app=kube-dns`
3. Review CoreDNS logs: `kubectl logs -n kube-system -l k8s-app=kube-dns`
4. Check DNS query rate / throttling in Cloud Monitoring
5. Verify service exists: `kubectl get service <service-name>`

## Fix Steps
1. **Restart CoreDNS pods** if they're in bad state:
   ```bash
   kubectl rollout restart deployment/coredns -n kube-system
   ```
2. **Scale CoreDNS** if under load:
   ```bash
   kubectl scale deployment/coredns -n kube-system --replicas=4
   ```
3. **Add DNS caching** in pod (ndots reduction):
   ```yaml
   dnsConfig:
     options:
       - name: ndots
         value: "1"
   ```
4. **Check and increase DNS query rate limit** in CoreDNS ConfigMap

## Follow-up Actions
- Add CoreDNS error rate alert
- Review DNS caching configuration
- Consider node-local DNS caching (NodeLocal DNSCache)
- Document expected DNS query volumes
