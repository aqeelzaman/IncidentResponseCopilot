# Runbook: gRPC Deadline Exceeded

**Service Tag:** all-services
**Severity Tag:** P2

## Symptoms
- gRPC status code DEADLINE_EXCEEDED (code 4)
- "context deadline exceeded" in logs
- Requests timing out before receiving response
- Often accompanies downstream slowness

## Diagnostic Steps
1. Check which gRPC method is timing out
2. Measure actual server-side processing time vs client deadline
3. Check for upstream dependency slowness causing deadline propagation
4. Verify deadline values in client configuration
5. Check for deadline not being propagated correctly through call chain

## Fix Steps
1. **Increase client deadline** if server is legitimately slow:
   ```python
   stub.MyMethod(request, timeout=30)  # increase from current value
   ```
2. **Optimize server handler** if genuinely slow
3. **Implement deadline propagation** across service boundaries
4. **Add server-side timeouts** to prevent runaway handlers

## Follow-up Actions
- Add gRPC deadline exceeded rate alert
- Review deadline values across all gRPC clients
- Implement deadline propagation middleware
- Add gRPC reflection for easier debugging
