## 12. Scalability and future enhancements

### 12.1 Current limitations

One Gunicorn worker; SQLite; one appliance; no failover; several features
without live verification (see `Implementation_Status.md`).

### 12.2 Performance recommendations [R]

- Raise the Data polling interval and Check interval for large networks.
- Shorter diagnostic retention to bound `history.db`.
- Schedule discovery off-hours.

### 12.3 Scalability [R]

- Move to PostgreSQL if write contention appears (requires code and
  migration work; not planned).
- Separate the scheduler into its own process to allow multiple web workers.
- Nagios distributed checking for remote sites.

### 12.4 Additional hardware or software [R]

| Item | Purpose | Importance |
|---|---|---|
| UPS | Avoid database corruption on power loss | High |
| Off-host backup target (NAS) | Survive server loss | High |
| TLS certificate | Encrypt UI traffic and credentials | High |
| Secondary SMTP relay | Alert delivery if the primary fails | Medium |
| Standby appliance | Faster cold-standby recovery | Medium |

### 12.5 Security improvements [R]

HTTPS everywhere; login rate limiting; dependency scanning; SNMPv3 credential
transport fix; MFA for administrators.

### 12.6 Proposed enhancements

Email-based password recovery (open gap), forecast notifications (follow-up),
History page wiring for custom ranges (#142), acknowledgement filter on host
and service tables, custom plugin upload decision.
