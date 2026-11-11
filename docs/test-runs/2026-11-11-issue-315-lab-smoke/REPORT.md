# Test run: issue-315-lab-smoke

| | |
|---|---|
| Date | 2026-11-11 |
| Commit tested | `4e86fb66` (branch `issue-315-lab-smoke-plugin-alert`, clean tree) |
| Plan | none; the acceptance list of issue #315 |
| Tester / executor mode | Scripted (`scripts/lab smoke`), run by an AI agent |
| Environment | Local Docker lab (`scripts/lab up`, fresh build), lab network `10.78.0.0/24`, database state fresh |
| Raw evidence | Terminal output only; nothing is retained outside this report |

## Result

**Overall: Pass.** `scripts/lab smoke` ran 16 checks: 16 passed, 0 failed. The seven existing discovery and host checks still pass; the new nine are below.

## Cases

| Check | Result | Notes |
|---|---|---|
| Plugin `check_ssh` is in the Plugin Manager | Pass | HTTP 200 |
| Enable `check_ssh` | Pass | HTTP 200 |
| `check_ssh` created services and they report OK | Pass | 5 services OK (one per target) |
| `scripts/lab break web01 ssh` | Pass | `sshd: stopped` |
| A new alert appears in the active alerts feed | Pass | `ssh-22-tcp` on the web01 host |
| `scripts/lab fix web01 ssh` | Pass | `sshd: started` |
| The alert clears after the service is back | Pass | |

## Deviations from the plan

None. Discovery took 128 s.

## Follow-up

- None. The checks are not in CI (decided in #306).

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
