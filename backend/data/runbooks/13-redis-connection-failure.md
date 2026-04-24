# Runbook: Redis Connection Failure

**Service Tag:** api-gateway, checkout-service, session-service
**Severity Tag:** P2

## Symptoms
- Cache miss rate suddenly 100%
- "Connection refused" or "timeout" connecting to Redis
- Session-related failures if Redis stores sessions
- Latency spikes (falling through to DB on cache miss)

## Diagnostic Steps
1. Check Redis connectivity: `redis-cli -h <redis-host> ping`
2. Check Redis memory: `redis-cli INFO memory | grep used_memory_human`
3. Check maxmemory policy: `redis-cli CONFIG GET maxmemory-policy`
4. Check eviction stats: `redis-cli INFO stats | grep evicted_keys`
5. Check Redis Sentinel / Cluster status if HA setup

## Fix Steps
1. **If Redis OOM:** flush non-critical keys or increase maxmemory:
   ```bash
   redis-cli CONFIG SET maxmemory 4gb
   ```
2. **If connection refused:** restart Redis:
   ```bash
   kubectl rollout restart statefulset/redis
   ```
3. **If Redis Sentinel failover needed:**
   ```bash
   redis-cli -h sentinel-host -p 26379 SENTINEL failover mymaster
   ```
4. **Enable circuit breaker** so service degrades gracefully without cache

## Follow-up Actions
- Add Redis memory utilization alert (> 80%)
- Implement cache-aside with graceful degradation
- Review TTL policies to prevent unbounded memory growth
- Document Redis topology (standalone / sentinel / cluster)
