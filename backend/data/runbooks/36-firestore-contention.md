# Runbook: Firestore Contention and Hot Documents

**Service Tag:** user-service, notification-service
**Severity Tag:** P2

## Symptoms
- Firestore write latency spikes
- "Contention on a resource" errors in logs
- Counter or aggregate documents experiencing slow writes
- Errors on high-traffic documents updated by many writers

## Diagnostic Steps
1. Identify hot documents from Firestore monitoring metrics
2. Check write frequency to specific documents
3. Review query patterns for collection group queries without indexes
4. Check Firestore usage limits (1 write/second per document)

## Fix Steps
1. **Implement distributed counter** for frequently-updated values:
   ```python
   # Split counter into N shards
   shard_ref = db.collection('counters').document(f'counter_{random.randint(0,N-1)}')
   shard_ref.update({'count': firestore.Increment(1)})
   ```
2. **Batch writes** where possible (up to 500 ops per batch)
3. **Add missing indexes** for slow collection queries:
   ```bash
   gcloud firestore indexes composite create --collection-group=orders \
     --field-config field-path=userId,order=ASCENDING \
     --field-config field-path=createdAt,order=DESCENDING
   ```

## Follow-up Actions
- Review data model for hot document anti-patterns
- Add Firestore quota utilization monitoring
- Document Firestore limits in service design guidelines
