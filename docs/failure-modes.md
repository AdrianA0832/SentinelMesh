# Failure Modes

How SentinelMesh handles breaking.

## Storage Failure
- **Symptom**: `data/` directory becomes read-only.
- **Response**: System enters "Read-Only Mode". Scans continue in memory but result in warnings. No crash.
- **Indicator**: Health check returns `storage: "readonly"`.

## Network Failure
- **Symptom**: Network card missing or disconnected.
- **Response**: Scanner returns empty list. Baseline assumes "Normal" until data returns.
- **Indicator**: Audit log records "Scan failed".

## Email Failure
- **Symptom**: SMTP server down.
- **Response**: Alert is logged to `alerts.csv`. Error logged to audit log. Application continues running.
