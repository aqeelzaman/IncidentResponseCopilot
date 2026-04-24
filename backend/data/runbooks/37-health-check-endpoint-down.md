# Runbook: Health Check Endpoint Down

**Service Tag:** all-services
**Severity Tag:** P2

## Symptoms
- Kubernetes liveness/readiness probes failing
- Pods being restarted or removed from service endpoints
- Health check endpoint returns 500 or times out

## Diagnostic Steps
1. Manually check health endpoint: `curl http://<pod-ip>:<port>/health`
2. Check what dependencies the health check validates
3. Look for health check timing out due to DB/cache connectivity
4. Check if health check has excessive dependencies (should be lightweight)
5. Review recent code changes to health check endpoint

## Fix Steps
1. **If health check depends on DB:** fix DB connectivity (see DB runbooks)
2. **If health check is too strict:** simplify to just return 200:
   ```python
   @app.get("/health")
   async def health():
       return {"status": "ok"}  # No dependency checks
   ```
3. **Adjust probe settings** if service is slow to initialize:
   ```yaml
   readinessProbe:
     initialDelaySeconds: 30
     failureThreshold: 10
     periodSeconds: 5
   ```
4. **Separate liveness from readiness:** liveness = alive, readiness = ready for traffic

## Follow-up Actions
- Define health check standard: liveness vs readiness vs startup probes
- Add deep health check endpoint separately from basic liveness
- Document health check implementation requirements
