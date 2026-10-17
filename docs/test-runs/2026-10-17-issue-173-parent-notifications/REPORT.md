# Test run: issue-173-parent-notifications

| | |
|---|---|
| Date | 2026-10-17 |
| Commit tested | Live driver `f45126c0a052251ea857d8a14eafaad8999558c2`; unchanged driver after main sync `c65c3ba4`; later edits are documentation only |
| Plan | [Manual Topology Acceptance, #173 cases](../../../server/tests/plans/MANUAL_TOPOLOGY_ACCEPTANCE.md#one-attempt-notification-contract-173-option-a) |
| Tester | Codex |
| Environment | Disposable Ubuntu 22.04 Docker images, real Nagios Core 4.5.11, two internal routed bridges inside `10.77.0.0/28`; no application database or external targets |
| Images | Appliance `8e36a8d8d077b086f9aac136d2735009eb92840d800ce0210a51d66aa3677fcd`; router `947f6760588436fab1e59a3a1b0c4ce75c17582d999c8bc9c971e7024b6b833b` |
| Raw evidence | Local host `/home/paeng/pinpoint-test-results/issue-173-20261017-active/`, with `single/` and `redundant/`; console `/tmp/pinpoint173-active-console.log`; full gate `/tmp/pinpoint173-verify-all-current.log` |

## Result

**Overall: Pass for the #173 native-engine acceptance scope.** Both single and
redundant-parent trials reproduced a temporary child HARD DOWN notification before
HARD UNREACHABLE, with no-parent DOWN and recovery controls. All owned resources
were removed. No production monitoring settings changed.

Totals: Pass 5, Fail 0, Blocked 0, Skipped 0. Full repository checks and PR CI are
recorded separately from these five observed live cases.

## Exact settings and method

| Setting | Value |
|---|---|
| Nagios Core | 4.5.11, stock binary in the disposable appliance image |
| `interval_length` | 2 seconds |
| Host `check_interval` | 60 units = 120 seconds |
| Host `retry_interval` | 1 unit = 2 seconds; no additional confirmation attempt with maximum 1 |
| Host `max_check_attempts` | 1 |
| `cached_host_check_horizon` / `cached_service_check_horizon` | 15 / 15 seconds |
| `status_update_interval` | 1 second |
| Active/passive checking | Global and per-host active checking enabled; passive host/service checks disabled; forced active checks via the external command FIFO control ordering |
| Host command | Real `check_ping`, one packet, warning/critical thresholds `5000,100%`, plugin timeout argument 2 seconds; Core `host_check_timeout=4` |
| Notifications | Enabled; host options `d,u,r`; period 24×7; first delay 0; interval 0 (no repeat); sink contact uses `/bin/true` |
| Other engine policy | Global flap detection and event handlers disabled, retention disabled; no service check drives host state |
| Parent definitions | Single: child has `parents parent-a`; redundant: `parents parent-a,parent-b`; no-parent control uses the same physical target with no `parents` directive |

Every trial starts with fresh active HARD UP results, not initial default UP
snapshots. Immediately before router power-off, a fresh UP check primes the
remaining parent's cache. The failing child is checked before the parent loss is
confirmed. Subsequent forced active checks confirm the parent and child states.
This is a controlled reproduction within the regular 120-second check interval,
not a measurement of normal scheduling latency or a promised convergence timeout.
The remaining parent's UP status is present in the transient-child snapshot.

Physical route loss is caused by stopping the owned router container. Failures
were reported by real ICMP checks (including Core's four-second timeout), not
injected passive results. The two-parent trial explicitly moves both static
routes to the alternate router before the first router is stopped. Parent links
alone do not implement failover. No scans or host route commands were run.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| P173-01 | Pass | Real Core validation succeeds with zero errors; initial host observations all have `state_type=1` (HARD), `current_state=0` (UP) and nonzero active-check timestamps. `validation.txt`, `version.txt`, `settings.json`, `objects.cfg`, `observations.json`, root `metadata.json`. | — |
| P173-02 | Pass | Single parent: child HARD DOWN notification at epoch 1792220691, parent HARD DOWN at 1792220697, child HARD UNREACHABLE notification at 1792220703, child HARD UP at 1792220713. `single/state-and-notification-events.log`, `single/observations.json`. | — |
| P173-03 | Pass | With parent-a HARD DOWN, explicit routing through parent-b kept child HARD UP. After parent-b power-off, child HARD DOWN notification at 1792220741, parent-b HARD DOWN at 1792220747, child HARD UNREACHABLE notification at 1792220752. `redundant/observations.json`, `redundant/state-and-notification-events.log`. | — |
| P173-04 | Pass | Same-target no-parent definition stayed HARD DOWN in both outages; restoring the selected router restored both definitions to HARD UP. Single recovery child/no-parent at 1792220713/1792220715; redundant recovery at 1792220759/1792220761. Both `observations.json` and event logs. | — |
| P173-05 | Pass | Both `cleanup.json` files contain empty container/network lists; final Docker inventory contains no `pinpoint173-` resources. Shared lab containers were untouched. | — |

## Deviations from the plan

Earlier controlled runs with normal scheduled host checks disabled also passed
single/redundant cases. The final reported driver keeps ordinary active checking
enabled to avoid relying on disabled scheduling. Those earlier raw runs remain
in `/tmp/pinpoint173-run1/` and
`/home/paeng/pinpoint-test-results/issue-173-20261017-final/`.
Two attempted overlapping starts were refused by Docker's address-pool overlap
check before any live cases ran; their cleanup records show no owned resources.
The final run began after the earlier trial finished cleanup.

The fixture uses native host definitions to isolate Core semantics; it does not
repeat the parent editor or generated-config API journeys from #117. Existing
parent-generation regressions were run separately (39 passed). Main #118 was
merged during verification; its service notification dependencies and operator
text are preserved. The obsolete pre-merge full gate was stopped and the combined
tree is verified separately.

## Follow-up

- Product choice: Option A accepted. No application or installer cache, retry,
  notification-delay or one-attempt restriction change is required.
- The notification sink proves Core dispatch, not SMTP transport or inbox receipt.
  Browser, installer deployment and new application runtime behavior are outside
  this native-engine acceptance scope.
- Full local `scripts/verify.sh all` passes on the combined branch: 3774 backend passed / 14 skipped, 864 frontend passed, build and lint passed (30 existing lint warnings and the bundle-size advisory). Documentation checks were rerun after the report edits. Final PR CI is tracked on [PR #192](https://github.com/esfen14/Pinpoint/pull/192); no further native-engine reproduction or product decision remains for #173.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
