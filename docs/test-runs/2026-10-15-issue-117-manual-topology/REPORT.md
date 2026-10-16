# Test run: issue-117-manual-topology

| | |
|---|---|
| Date | 2026-10-15 |
| Commit tested | Application source `051abed5ff113827a8a2a00309b0e4b6f5aa9e0d`; uncommitted changes during final live run were documentation only |
| Plan | [Manual Topology Acceptance](../../../server/tests/plans/MANUAL_TOPOLOGY_ACCEPTANCE.md) |
| Tester | Codex |
| Environment | Disposable Docker containers from Ubuntu 22.04 appliance image; real Nagios Core 4.5.11; two isolated internal bridges in `10.77.0.0/28`; private system/history SQLite databases upgraded through `b117d9a2c041` |
| Raw evidence | Local host: `/tmp/issue117-live-a2ab65f9/`; driver `/tmp/issue117-live.py`, adapter `/tmp/issue117-inner.py`, console `/tmp/issue117-live-active-checks.log`; verification `/tmp/issue117-all.log`; browser fixture `/tmp/issue117-browser2.log` and `/tmp/issue117-topology-dark.png` |

## Result

**Overall: Partial.** The implementation's routed reachability, real Nagios
validation/apply, lifecycle and default-three-attempt notification cases passed.
Local full verification and frontend/browser fixture checks passed. Final PR CI
and human review remain outside this report. A separate one-attempt notification
guarantee needs a decision in [#173](https://github.com/esfen14/Pinpoint/issues/173).

Totals: Pass 8, Fail 0, Blocked 0, Skipped 1.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| P117-01 | Pass | Populated multi-bind upgrade/downgrade; graph/API/permissions, zero/one/multiple rendering, merge/retire/automatic retirement and actual shared-writer rollback tests. Latest focused proof: 38 passed (`/tmp/issue117-final-parent-proof.log`). Earlier broader focused regression: 308 passed. | — |
| P117-02 | Pass | Authenticated Flask route handlers in the private container applied one/two-parent changes through the real shared writer and Nagios binary, not a mocked validator. `validation.txt`, saved `api-*.txt`, `final-validation.txt`. No-parent baseline validated. | — |
| P117-03 | Pass | Unit integration tests exercised the real shared writer with failed validation/reload at process boundary, exact host-file rollback and parent-set rollback. A successful reload followed by audit failure also restored graph and original config. Nagios subprocess failures are injected for these failure-path tests; they are not real-daemon outage trials. | — |
| P117-04 | Pass | Actual checked HARD baseline: all devices UP. Powered off the owned single parent container: parent-a DOWN, child-a and child-b UNREACHABLE. `single-parent-notifications.log` contains parent DOWN and child UNREACHABLE notifications, no child DOWN. Powered on parent; all recovered. | — |
| P117-05 | Pass | Applied two parents, then explicitly moved static routes to the alternate router before powering off parent-a: children remained UP. Powering off parent-b too made both children UNREACHABLE; restoration recovered all. Recorded actual HARD states and nonzero check times, not initial/soft snapshots. `alternate-path-up.json`, `both-parents-off.json`, `redundant-recovery.json`, `nagios.log`. This final run had no child DOWN notifications. | — |
| P117-06 | Pass | Paused one parent via real API/reconciler/writer: stored edges retained, omission reason returned and only the other parent rendered. Paused both: no parents directive. Resumed both successfully. `api-*.txt`; final candidate validated. | — |
| P117-07 | Pass | Real API merge re-pointed/deduplicated selected parents, retire cleared links and final graph edges were empty. Real Nagios validation passed. Invalid merge-cycle rejection is covered by isolated API regression. | — |
| P117-08 | Pass | Existing drawer/table tests unchanged; route tests updated for the owner's topology scope reversal. Focused frontend: 82 tests passed, followed by added draft-preservation proof. Browser fixture used real React Flow with intercepted API: node selection, multiple parents, clear/reload persistence, disabled dragging and read-only controls passed without page errors. Visually inspected screenshot; all roots/shared child fit after opening the detail panel. | — |
| P117-09 | Skipped | Local `scripts/verify.sh all` passed: 3038 backend passed / 14 skipped, 653 frontend passed; build/docs/lint passed with 30 lint warnings and bundle-size warning. That gate began before the minor applied/unchanged response and fit-on-selection refinements now in `051abed5`; current parent/migration focus (38 passed), frontend gate and browser smoke were rerun after them. Final PR CI/human approval are not established by this report. | [#117](https://github.com/esfen14/Pinpoint/issues/117) |

## Deviations from the plan

- The original single-gateway/two-child trial was extended to two actual routers
  between separate bridges. No shared Docker targets, VM, host routes or external
  devices were changed. Owned containers/networks were removed in `finally`.
- Timing used 2-second Nagios interval units and the application's default three
  attempts. Active checks were requested through Nagios's external command FIFO
  while waiting for HARD states, avoiding reliance on initial UP snapshots or the
  minimal lab daemon's scheduler. No passive check results were injected.
- Setup attempts needed a stock local service (Nagios refuses a zero-service
  configuration) and validation as the same user that owns temporary config files;
  a root validator drops privileges and could not read the private temporary file.
- Earlier deliberately accelerated one-attempt trials observed transient child
  DOWN before UNREACHABLE. A default-attempt draft initially looked at soft states
  too early, then waited for a parent HARD state without actively scheduling checks.
  Those attempts do not establish notification acceptance. The final driver waits
  for actual HARD checks and preserves the earlier evidence in the follow-up.
- Nagios can reuse cached parent results; parent links do not promise universal
  immediate notification suppression for every cache/retry configuration. Official
  [host checks](https://assets.nagios.com/downloads/nagioscore/docs/nagioscore/4/en/hostchecks.html)
  and [cached checks](https://assets.nagios.com/downloads/nagioscore/docs/nagioscore/4/en/cachedchecks.html)
  explain the engine behavior. No production retry/cache setting was changed.
- Notification dispatch was observed in Nagios logs; a disposable sendmail sink
  consumed messages. SMTP delivery/inbox receipt was not tested. No real secrets
  or email account were configured.
- The browser smoke intercepted API responses; it is not a browser walkthrough
  against the routed backend. Actual backend/writer behavior was exercised
  separately through the Flask route handlers inside the private container.

## Follow-up

- [#173](https://github.com/esfen14/Pinpoint/issues/173): decide the one-attempt
  child-DOWN notification guarantee and any separately approved Nagios main config
  or operator guidance changes. Stop this thread rather than silently expand #117.
- Final CI and human review/approvals are tracked on the implementation PR.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
