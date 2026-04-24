# Runbook: BigQuery Quota Exceeded

**Service Tag:** analytics-service, reporting-service
**Severity Tag:** P2

## Symptoms
- BigQuery jobs failing with "Quota exceeded" errors
- `quotaExceeded` error code in BigQuery API responses
- Dashboards and reports failing to load data

## Diagnostic Steps
1. Check quota usage in GCP Console → IAM → Quotas → BigQuery
2. Identify which quota is exceeded (concurrent queries, bytes processed, etc.)
3. Look for runaway queries or missing LIMIT clauses
4. Check if a new report or analytics feature is consuming excess quota

## Fix Steps
1. **Request quota increase** in GCP Console (takes ~2 business days)
2. **Kill expensive running jobs:**
   ```bash
   bq ls -j --all | grep RUNNING
   bq cancel <job_id>
   ```
3. **Add query cost controls:** set `maximumBytesBilled` on queries
4. **Add result caching** for repeated identical queries
5. **Use table partitioning and clustering** to reduce bytes scanned

## Follow-up Actions
- Add BigQuery quota utilization alert (> 80%)
- Implement query cost governance (maximum bytes billed per query)
- Review and optimize expensive queries
- Consider BigQuery Reservations for predictable capacity
