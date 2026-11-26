## 7. Best practices

### 7.1 Recommended usage

- Start each shift on the **Dashboard** and clear unacknowledged critical
  alerts first.
- Always write a useful acknowledgement comment: what, who, expected time.
- Use maintenance windows for planned work instead of pausing devices or
  turning on Maintenance Mode.
- Set parent devices for switches and routers so outages are easier to read.
- Keep the scan frequency modest; daily is usually enough for a stable
  network. **Tip**, not a product default.

### 7.2 Data privacy and account security

- Never share your account. Each acknowledgement and change is recorded under
  your name.
- Sign out when you leave a shared computer.
- Choose a long, unique password. Ask your administrator to switch on the
  strong password policy.
- Give people the lowest role that lets them do their job.
- Pass temporary passwords privately, never in a group chat or ticket.

### 7.3 Handling information

- Reports and exports can contain device names and addresses. Store them only
  where your organisation allows.
- Do not paste SSH passwords, SNMP communities or other secrets into
  acknowledgement comments or maintenance reasons.

### 7.4 Common mistakes to avoid

| Mistake | Why it matters |
|---|---|
| Leaving Maintenance Mode on | PinPoint stops automatic scans and plugin checks (backups continue) |
| Scanning networks you do not own | May break policy or law |
| Acknowledging without a comment that explains anything | Others cannot act on it |
| Disabling a plugin to silence one device | Stops that check on every device |
| Ignoring an old **Data Updated** time | You may be reading old data |
