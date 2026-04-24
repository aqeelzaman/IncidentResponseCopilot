# Runbook: Payment Service Timeout and 503 Errors

**Service Tag:** payment-service, checkout-service
**Severity Tag:** P1

## Symptoms
- Orders failing at payment step
- payment-service returning 503 or timing out
- Checkout flow broken end-to-end
- Revenue impact immediately visible in business dashboards

## Diagnostic Steps
1. Check payment-service health endpoint
2. Check payment-service logs for upstream provider errors
3. Verify payment provider status page (Stripe, Braintree, etc.)
4. Check payment-service DB connectivity
5. Look for connection pool exhaustion in payment-service

## Fix Steps
1. **If payment provider is down:** enable fallback / deferred payment mode
2. **If connection pool exhausted:** see DB connection pool runbook
3. **Scale payment-service:**
   ```bash
   kubectl scale deployment/payment-service --replicas=20
   ```
4. **Enable retry with idempotency key** (ensure payments aren't double-charged)
5. **Activate incident bridge** with payment provider support

## Follow-up Actions
- Implement payment provider fallback (primary + backup provider)
- Add payment success rate alert (< 99% success rate triggers P1)
- Test payment provider failover scenario quarterly
- Ensure idempotency keys are used for all payment retries
