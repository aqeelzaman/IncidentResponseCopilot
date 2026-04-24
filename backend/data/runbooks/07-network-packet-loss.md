# Runbook: Network Packet Loss

**Service Tag:** all-services
**Severity Tag:** P1

## Symptoms
- Intermittent request failures with connection reset errors
- TCP retransmit rate elevated
- `ping` shows packet loss between pods
- Distributed traces show random timeout spikes

## Diagnostic Steps
1. Test connectivity: `ping -c 100 <destination-ip>` — look for packet loss
2. Check TCP retransmits: `ss -s` or `netstat -s | grep retransmit`
3. Identify affected nodes: `kubectl get nodes -o wide`
4. Check node network interface errors: `ip -s link show eth0`
5. Review GCP VPC flow logs for dropped packets

## Fix Steps
1. **Cordon and drain affected node** if node-specific:
   ```bash
   kubectl cordon <node-name>
   kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data
   ```
2. **Increase TCP retransmit timeout** as temporary relief:
   ```bash
   sysctl -w net.ipv4.tcp_retries2=5
   ```
3. **File GCP support ticket** if underlying network issue
4. **Enable TCP keepalive** on connection-heavy services

## Follow-up Actions
- Add network packet loss monitoring in Cloud Monitoring
- Review GCP network quota limits
- Consider Network Policy audit
- Document node replacement runbook
