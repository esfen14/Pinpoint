# Test run: issue-79-preflight

| | |
|---|---|
| Date | 2026-10-14 |
| Commit inspected/tested | `3b2dcc0218f87b07956a428877d0b070a1a617a6` |
| Plan | Issue [#79](https://github.com/esfen14/Pinpoint/issues/79), VM delivery finish condition |
| Tester | Codex |
| Environment | Linux development environment; user confirms Docker only; no accessible lab |
| Raw evidence | Local, ignored `test-results/issue79-all.log`, `test-results/issue79-backend.log`, `test-results/issue79-frontend.log`, `test-results/issue79-docs.log` |

## Result

**Overall: Blocked for live acceptance.** The prerequisites were checked; no
application behavior was exercised on a live lab. Isolated tests are evidence
for their mocked contracts only and cannot establish real Nagios or inbox delivery.

Totals: Pass 0, Fail 0, Blocked 3, Skipped 0.

## Cases

| Case | Result | Notes (observed prerequisite) | Issue |
|---|---|---|---|
| VM availability | Blocked | `scripts/vmlab status` reports `VBoxManage not found`. User confirms only Docker exists here. | [#79](https://github.com/esfen14/Pinpoint/issues/79) |
| Docker alternative | Blocked | `docker ps` is denied at the Docker socket; `sudo -n docker ps` requires interactive authentication. No container changes performed. | [#79](https://github.com/esfen14/Pinpoint/issues/79) |
| VM save, validation and email comparison | Blocked | No accessible VM or mailbox evidence. Must observe selected recipients on one host and default recipients on another, including `nagios -v`, before sign-off. | [#79](https://github.com/esfen14/Pinpoint/issues/79) |

## Deviations from the plan

No live save, Nagios execution, notification dispatch or inbox verification was
attempted. The implementation remains on a draft PR; this report establishes no
product pass and updates no QA result ledger.

## Follow-up

- Run the VM save/validation/delivery acceptance on an exclusively reserved lab
  with configured mail transport and controlled test inboxes.
- Keep issue #79 open and its live finish-condition checkbox unticked until that
  comparison is observed.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
