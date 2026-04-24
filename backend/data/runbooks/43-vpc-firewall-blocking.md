# Runbook: VPC Firewall Rule Blocking Traffic

**Service Tag:** all-services
**Severity Tag:** P1

## Symptoms
- Connection timeouts (not refused) between services
- Traffic suddenly unable to reach a service that was working
- Firewall rule change in recent audit log
- `gcloud compute firewall-rules list` shows blocking rule

## Diagnostic Steps
1. Test connectivity: `nc -zv <destination-ip> <port>`
2. Check VPC flow logs for dropped packets
3. Review recent firewall rule changes in Cloud Audit Log
4. List active firewall rules: `gcloud compute firewall-rules list --filter="network=<vpc>"`
5. Check firewall rule priorities (lower number = higher priority)

## Fix Steps
1. **Identify blocking rule** and its source
2. **Add allow rule** with higher priority (lower number):
   ```bash
   gcloud compute firewall-rules create allow-svc-traffic \
     --network=<vpc> \
     --allow=tcp:<port> \
     --source-tags=<source-tag> \
     --target-tags=<target-tag> \
     --priority=900
   ```
3. **Delete incorrect blocking rule** if it was accidentally created:
   ```bash
   gcloud compute firewall-rules delete <rule-name>
   ```

## Follow-up Actions
- Store firewall rules in Terraform and use IaC for changes
- Add firewall rule change alerts
- Document required firewall rules per service
- Regular firewall rule audit against least-privilege policy
