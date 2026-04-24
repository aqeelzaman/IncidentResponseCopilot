# Runbook: Memory Leak Detection and Remediation

**Service Tag:** all-services
**Severity Tag:** P2

## Symptoms
- Memory utilization grows steadily over hours/days
- Pod eventually OOMKilled and restarted
- Memory never released despite traffic being normal
- GC pressure increasing over time (JVM services)

## Diagnostic Steps
1. Plot memory utilization over 24h — steady upward trend indicates leak
2. Correlate memory growth with specific traffic types or time of day
3. Take heap dump: `kubectl exec <pod> -- jmap -dump:format=b,file=/tmp/heap.hprof <pid>`
4. Analyze heap dump with Eclipse MAT or JProfiler
5. Check for unbounded caches, session storage, listener registrations

## Fix Steps
1. **Immediate:** add memory limit and restart schedule (quick mitigation)
2. **Roll back** if leak introduced in recent deploy
3. **Fix identified leak:** typically unbounded HashMap, EventListener not removed,
   ThreadLocal not cleared, or large object in static field
4. **Add heap dump on OOM:** `-XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/tmp`

## Follow-up Actions
- Add memory growth rate alert (> 5% per hour sustained)
- Add automated heap dump collection on OOM
- Include memory profiling in pre-release testing
- Implement scheduled pod restarts as workaround during investigation
