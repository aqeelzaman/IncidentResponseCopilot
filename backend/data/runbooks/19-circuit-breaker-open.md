# Runbook: Circuit Breaker Open

**Service Tag:** checkout-service, order-service, api-gateway
**Severity Tag:** P2

## Symptoms
- Service returning fast-fail errors (not timeout errors)
- Circuit breaker state metric shows OPEN
- Logs: "Circuit breaker open for dependency X"
- Downstream service recovering but upstream still failing fast

## Diagnostic Steps
1. Check circuit breaker state: `curl http://service:8080/actuator/circuitbreakers`
2. Identify which dependency triggered the open state
3. Verify downstream dependency is actually healthy now
4. Check circuit breaker half-open probe results in logs
5. Review circuit breaker threshold configuration

## Fix Steps
1. **Force circuit breaker to half-open** to allow test probe:
   ```bash
   curl -X POST http://service:8080/actuator/circuitbreakers/<name>/state -d state=HALF_OPEN
   ```
2. **Manually reset** if downstream confirmed healthy:
   ```bash
   curl -X POST http://service:8080/actuator/circuitbreakers/<name>/state -d state=CLOSED
   ```
3. **Adjust thresholds** if too sensitive:
   - Failure rate threshold: 60% (increase from 50%)
   - Slow call rate threshold: 80%

## Follow-up Actions
- Add circuit breaker state change alerts
- Document circuit breaker thresholds for each dependency
- Review automatic recovery timing (half-open probe interval)
- Add circuit breaker dashboard to Grafana
