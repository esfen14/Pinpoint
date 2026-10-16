# Test run: issue-164-final-refresh

| | |
|---|---|
| Date | 2026-10-15 |
| Commit tested | `8c8ff608` |
| Plan | [Issue #164 E–H](https://github.com/esfen14/Pinpoint/issues/164); [initial acceptance and reproduction](../2026-10-15-issue-164-identity-review/REPORT.md) |
| Tester | Codex, actual automated executions |
| Environment | Fresh Ubuntu 22.04 Docker appliance, real Nagios Core 4.5.11, Python 3.14; Chromium / Playwright 1.64.0; controlled discovery observations and isolated target; exclusive `pinpoint-issue164` project, API/Vite bound to loopback 8164/5164 |
| Raw evidence | Local `/home/paeng/pinpoint-test-results/issue164/final-normal/`, `final-warning/`, `final-verify-all.log`; not committed |

## Result

**Overall: Pass for the scoped final implementation.** Fresh identity/address
responses now update the candidate summaries used in both selectors and merge
confirmation. The new regression failed on the older summary and passed after
the correction. The entire local gate and both real-browser/Nagios journeys were
repeated against this commit. CI and human approvals remain independently
observable PR gates; no reviewer approval is implied by this report.

Totals: Pass 6, Fail 0, Blocked 0, Skipped 0 scoped cases. Backend regression
separately reports 14 existing skips.

## Cases

| Case | Result | Observed evidence | Issue |
|---|---|---|---|
| Current candidate summaries | Pass | New interaction test reproduced an old name/IP in confirmation despite fresh comparison evidence. After propagating the evidence summary, selectors and confirmation use the current name/IP. Focused inventory/comparison suite: 51 passed (16 comparison tests); full frontend gate: 702 passed | #164 |
| Literal lookup and authorization | Pass | Six lookup tests passed, including permission guards, nonmonitored and retired records, bounds, literal wildcard rejection against a visible unmerged record, and a name containing a literal percent sign | #164 |
| Normal/notice browser journey | Pass | Fresh fixture recognized an IP move without another record/review, then generated an ambiguous review with insufficient candidates. Source outside Monitored, linked information notice, address evidence, discovered lookup, explicit choices, full confirmation, cancellation, keyboard focus, both themes, 560px layout, one submission and refreshed empty review all passed. `final-normal/issue164-comparison.png`, `issue164-light.png`, `issue164-dark.png`, `issue164-success.png` | #164 |
| Historical and monitoring postconditions | Pass | After normal merge: source Merged, target address retained, nonconflicting port moved, reviews resolved, source absent and target present in generated config. A direct query observed one genuine source status snapshot still under its original host name. Real `nagios -v`: 0 warnings/0 errors | #164 |
| Real saved configuration warning and recovery | Pass | Recreated only the disposable appliance and stopped its Nagios. Full browser journey returned config_ok false with a saved merge, exactly one POST, empty reviews and retained target identity/address. Restart/reconcile succeeded with changed true; all database/config postconditions passed and real Nagios validation again reported 0 warnings/0 errors. `final-warning/issue164-warning.png` | #164 |
| Final local gate | Pass | `scripts/verify.sh all`: 3302 backend passed, 14 existing skips; 702 frontend passed; docs/drift checks and TypeScript/Vite build pass; lint 0 errors and 28 existing warnings. [Implementation CI](https://github.com/esfen14/Pinpoint/actions/runs/38737994672) passed docs, backend and frontend on `8c8ff608`. Raw `final-verify-all.log` | #164 |

## Deviations from the plan

Same controlled Docker setup and boundaries as the initial report: no physical
DHCP, installer/systemd, production deployment or scale claim. Scheduler was
disabled before fresh migration and actual status polling was explicit. Both
final browser runs used unmodified real review/evidence/lookup/merge routes and
the real Nagios configuration path; no browser API response was intercepted.

The invalid-target test's evidence mock previously returned the record/state
for another device. It now returns the requested fixture's actual lifecycle;
all invalid-state assertions remain. No test was skipped or weakened.

## Follow-up

- Required checks and reviewer approvals are visible on [PR #176](https://github.com/esfen14/Pinpoint/pull/176).
- The disposable project was removed and the local Vite process stopped after
  capturing evidence; the shared Docker lab was untouched.
- No product defects remain from these scoped checks. No new dependency,
  permission or migration was added.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No raw addresses outside the documented lab range in this report
- [x] Raw screenshots/logs are referenced, not committed
