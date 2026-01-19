# Threat Model

Transparency is security. Here is what SentinelMesh protects against, and what it misses.

## What it Catches
- **New Devices**: Any device that talks on the local network (ARP).
- **Bursts**: Sudden spikes in connection counts (e.g. malwaaspam).
- **Persistence**: Devices that appear at odd times.
- **Changes**: Shifts in network environment (new router, subnet change).

## What it Misses
- **Encrypted Payloads**: We do not break SSL/TLS. We respect privacy.
- **Passive Listeners**: Devices that never transmit (sniffers) cannot be seen by ARP.
- **Deep Packet Inspection**: We do not look inside packets.
- **Cloud Threats**: We monitor the *device*, not the cloud account.

## Self-Defense
- **Read-Only Mode**: If the disk is locked, the tool degrades gracefully to a viewer.
- **Crash Safety**: Logging and Alerting modules catch all exceptions to prevent system exit.
- **Audit**: Every action (even mistakes) is logged.
