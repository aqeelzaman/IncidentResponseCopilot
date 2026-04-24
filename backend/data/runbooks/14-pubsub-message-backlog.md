# Runbook: Pub/Sub Message Backlog

**Service Tag:** notification-service, order-service
**Severity Tag:** P2

## Symptoms
- Cloud Pub/Sub subscription backlog growing (visible in GCP Console)
- Delayed order confirmations or notifications
- Consumer service logs show slow processing
- `subscription/num_undelivered_messages` metric elevated

## Diagnostic Steps
1. Check backlog size in Cloud Console → Pub/Sub → Subscriptions
2. Check consumer service CPU and throughput metrics
3. Look for processing errors in consumer logs
4. Verify message schema hasn't changed (backwards-compatible?)
5. Check for DLQ (dead-letter queue) growth

## Fix Steps
1. **Scale up consumer service:**
   ```bash
   kubectl scale deployment/notification-service --replicas=20
   ```
2. **Increase max messages per pull** in consumer config:
   ```python
   subscriber.subscribe(subscription_path, callback, flow_control=FlowControl(max_messages=100))
   ```
3. **If messages are poisoning consumer:** check DLQ and skip bad messages
4. **Purge backlog** (last resort, messages lost):
   ```bash
   gcloud pubsub subscriptions seek <subscription> --time=$(date -u +%Y-%m-%dT%H:%M:%SZ)
   ```

## Follow-up Actions
- Add subscription backlog alert (threshold: > 10k messages)
- Review consumer throughput vs producer rate
- Implement DLQ for failed message handling
- Consider message batching optimizations
