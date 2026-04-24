# Runbook: Rate Limiting / 429 Too Many Requests

**Service Tag:** api-gateway, external-clients
**Severity Tag:** P3

## Symptoms
- Clients receiving 429 Too Many Requests
- api-gateway logs show rate limit exceeded for specific client/IP
- Legitimate traffic being throttled during traffic spikes

## Diagnostic Steps
1. Identify which clients are hitting rate limits
2. Check current rate limit settings in api-gateway config
3. Determine if traffic is legitimate or abusive
4. Review rate limit headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`

## Fix Steps
1. **Temporary: increase rate limits** for legitimate high-traffic client:
   ```bash
   kubectl set env deployment/api-gateway RATE_LIMIT_RPM=10000
   ```
2. **Block abusive IPs** if attack pattern detected:
   ```bash
   gcloud compute security-policies rules create 1000 \
     --security-policy=api-gateway-policy \
     --expression="origin.ip == '<ip>'" \
     --action=deny-403
   ```
3. **Per-tenant rate limits:** update rate limit config in Redis

## Follow-up Actions
- Implement per-client rate limit tiers
- Add 429 rate spike alert
- Review rate limit values against SLA agreements
- Document rate limit policy and exception process
