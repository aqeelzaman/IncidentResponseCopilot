# Runbook: Kafka Consumer Lag

**Service Tag:** order-service, notification-service, analytics-service
**Severity Tag:** P2

## Symptoms
- Kafka consumer group lag growing
- Delayed message processing (orders not confirmed in time)
- Consumer pods CPU/throughput below max capacity
- Rebalance events in consumer logs

## Diagnostic Steps
1. Check consumer lag: `kafka-consumer-groups.sh --bootstrap-server <broker> --describe --group <group>`
2. Check consumer throughput metrics
3. Look for consumer rebalance events (processing pauses during rebalance)
4. Check partition count vs consumer count
5. Identify slow message processing (one message taking too long)

## Fix Steps
1. **Scale up consumer group:**
   ```bash
   kubectl scale deployment/order-consumer --replicas=20
   # Note: replicas should not exceed partition count
   ```
2. **Increase partitions** to allow more parallelism:
   ```bash
   kafka-topics.sh --bootstrap-server <broker> --alter --topic <topic> --partitions 40
   ```
3. **Fix slow consumer:** profile and optimize message processing
4. **Skip lag** if messages are too old and processing them would be harmful:
   ```bash
   kafka-consumer-groups.sh --bootstrap-server <broker> --group <group> --reset-offsets --to-latest --topic <topic> --execute
   ```

## Follow-up Actions
- Add consumer lag alert (threshold: > 10k messages)
- Review partition count vs expected peak consumer throughput
- Implement dead letter topic for failed messages
- Monitor rebalance frequency
