# Runbook: Cache Stampede (Thundering Herd)

**Service Tag:** checkout-service, api-gateway
**Severity Tag:** P2

## Symptoms
- Sudden spike in DB queries after cache expiry
- Cache miss rate spikes to 100% briefly
- DB CPU spikes in concert with cache miss events
- Occurs cyclically (every N hours when TTL expires)

## Diagnostic Steps
1. Correlate cache miss spike timing with cache TTL values
2. Check DB query rate at time of incident
3. Look for concurrent identical queries in DB slow log
4. Verify cache key TTL configuration

## Fix Steps
1. **Implement probabilistic early expiration** (cache key refreshed before expiry)
2. **Add request coalescing / mutex:** only one request rebuilds the cache
3. **Stagger TTL values** to prevent simultaneous mass expiry:
   ```python
   ttl = base_ttl + random.randint(0, base_ttl // 10)
   ```
4. **Pre-warm cache** before TTL expiry via background job
5. **Increase cache capacity** if eviction is causing stampede

## Follow-up Actions
- Implement cache stampede protection library (e.g., dogpile prevention)
- Add cache hit rate monitoring
- Review TTL values with traffic pattern data
- Document cache warming procedures for cache restart scenarios
