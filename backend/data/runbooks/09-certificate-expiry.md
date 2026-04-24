# Runbook: TLS Certificate Expiry

**Service Tag:** api-gateway, auth-service
**Severity Tag:** P1

## Symptoms
- TLS handshake failures
- Browser shows certificate expired error
- curl: "SSL certificate problem: certificate has expired"
- Sudden spike in failed HTTPS connections

## Diagnostic Steps
1. Check cert expiry: `echo | openssl s_client -connect <host>:443 2>/dev/null | openssl x509 -noout -dates`
2. List Kubernetes secrets: `kubectl get secrets | grep tls`
3. Check cert-manager status: `kubectl get certificaterequests,certificates`
4. Review cert-manager logs for renewal failures

## Fix Steps
1. **Renew certificate manually** (cert-manager):
   ```bash
   kubectl delete secret <tls-secret-name>  # triggers renewal
   kubectl annotate certificate <cert-name> cert-manager.io/issue-temporary-certificate="true"
   ```
2. **Manual renewal** (Let's Encrypt via certbot):
   ```bash
   certbot renew --force-renewal -d <domain>
   ```
3. **Update secret** with new cert:
   ```bash
   kubectl create secret tls <secret-name> --cert=cert.pem --key=key.pem --dry-run=client -o yaml | kubectl apply -f -
   ```
4. **Restart ingress controller** to pick up new cert

## Follow-up Actions
- Set up cert expiry monitoring alert (30-day and 7-day warnings)
- Verify cert-manager auto-renewal is working in staging
- Document certificate inventory and renewal schedule
- Consider using Google-managed certificates on GKE
