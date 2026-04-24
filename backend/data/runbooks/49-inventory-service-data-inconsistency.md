# Runbook: Inventory Service Data Inconsistency

**Service Tag:** inventory-service, checkout-service
**Severity Tag:** P2

## Symptoms
- Orders placed for out-of-stock items
- Inventory counts showing negative values
- Duplicate inventory decrements
- Inconsistency between inventory-service and order-service counts

## Diagnostic Steps
1. Check for duplicate order events in message queue
2. Review inventory transaction logs for ordering issues
3. Check if distributed transaction / saga pattern is working correctly
4. Look for missing compensating transactions after failures
5. Verify idempotency key handling in inventory service

## Fix Steps
1. **Reconcile inventory counts** from order history:
   ```sql
   UPDATE inventory SET quantity = (
     SELECT initial_quantity - SUM(ordered_quantity)
     FROM orders WHERE product_id = inventory.product_id AND status='confirmed'
   ) WHERE product_id = ?
   ```
2. **Pause new orders** for affected products while reconciling
3. **Replay missed events** from message queue if events were lost
4. **Add compensating transactions** for the saga failure path

## Follow-up Actions
- Implement optimistic locking for inventory updates
- Add inventory count reconciliation job (runs every 15 min)
- Add alert for negative inventory values
- Review distributed transaction pattern implementation
