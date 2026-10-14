# Test run: issue-141-docker-history

| | |
|---|---|
| Date | 2026-10-14 |
| Commit tested | `43c1be42` |
| Plan | Ad hoc #141 host episode list/filter/detail check; no formal lab plan |
| Tester | OpenCode agent |
| Environment | Local Docker lab, Ubuntu 22.04 appliance, Nagios Core 4.5.11, isolated 10.78.0.0/24, fresh databases; `scripts/lab up` then `scripts/lab smoke` |
| Raw evidence | Local lab API responses observed in session; no persistent raw evidence archive |

## Result

**Partial.** A real Nagios host went DOWN, was acknowledged, recovered, and went DOWN again. A fresh read of history list, detail and both filters correctly associated the first acknowledgement only with the earlier problem episode. Service episode and manual-unacknowledge paths were not run on this appliance.

Totals: Pass 2, Fail 0, Blocked 0, Skipped 2.

## Cases

| Case | Result | Notes | Issue |
|---|---|---|---|
| Fresh lab readiness | Pass | `scripts/lab smoke`: 9 passed, 0 failed; five targets and localhost Up after discovery. | — |
| Host problem → acknowledgement → recovery → new problem | Pass | `web01` target stopped, host DOWN, app-side acknowledgement saved and Nagios sync confirmed; target restarted, host UP, then stopped again. A fresh history list showed the two earlier DOWN transitions acknowledged and both later DOWN transitions unacknowledged; the UP recovery was unacknowledged. Detail returned the first episode's comment for earlier events and null for later events; acknowledged-only and unacknowledged-only filters partitioned the same rows correctly. Target restored. | #141 |
| Service episode cycles | Skipped | Requires enabling a plugin-backed service and repeat fault injection; not attempted in this run. Isolated host/service tests pass but are not live evidence. | #141 |
| Manual unacknowledge | Skipped | Not exercised on the Docker appliance in this run. | #141 |

## Deviations from the plan

No formal case plan. The first check used a list response captured before the acknowledgement and asserted against later detail, producing a stale-list assertion failure. Re-reading the list after the full cycle showed the expected association; no product failure was reproduced.

## Follow-up

- Defects found: none confirmed.
- Cases to repeat: service episodes and manual unacknowledge, ideally with a dedicated test harness and durable sanitized evidence.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is described without raw responses or secret-bearing logs
