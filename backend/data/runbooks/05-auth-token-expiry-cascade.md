# Runbook: Auth Service Token Expiry Cascade

**Service Tag:** auth-service, api-gateway
**Severity Tag:** P1

## Symptoms
- Sudden spike in 401/403 errors across all services
- Auth service logs show "token validation failed", "expired token"
- High load on auth-service (all services re-authenticating simultaneously)
- Token refresh storms visible in auth-service request rate

## Diagnostic Steps
1. Check auth-service error rate and latency
2. Identify token expiry times: `kubectl get secret jwt-secret -o yaml | grep expiry`
3. Check token refresh queue depth
4. Look for bulk token expiry (all tokens issued at same time)
5. Verify auth-service DB connectivity

## Fix Steps
1. **Emergency token re-issuance:**
   ```bash
   kubectl exec -it auth-service-pod -- /bin/sh -c "python manage.py reissue_tokens --all"
   ```
2. **Stagger token expiry** to prevent future cascades:
   - Set `TOKEN_EXPIRY_JITTER=3600` environment variable
3. **Scale auth-service** to handle refresh storm:
   ```bash
   kubectl scale deployment/auth-service --replicas=20
   ```
4. **Enable token caching** in api-gateway to reduce auth-service load

## Follow-up Actions
- Implement token expiry jitter (randomize expiry within ±30min window)
- Add auth-service capacity alert
- Review token refresh thundering herd patterns
- Document token lifecycle and rotation procedures
