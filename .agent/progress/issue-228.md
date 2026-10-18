# Issue #228: TC-RPT-01: Host Availability report shows state Unknown, no last check, and unmonitored hosts

Branch: `issue-228-host-current-state`
Status: in-progress
<!-- Status is one of: in-progress | blocked | ready-for-review -->

## Finish condition

Copied from the issue. Tick an item only when a check proves it.

- [x] Each host row shows its real current state, last check and last state change from a real source, and the summary cards count Up and Down correctly. (The issue's alternative, changing the spec instead, was ruled out by the lab owner: "Show real data".) Proof: `server/tests/unit/test_report_availability.py` (`TestReportAvailabilityCurrentStatus`, `TestHostsByOsCurrentStatus`), `test_host_current_status.py`, `client/src/test/HostAvailabilityCurrentState.test.tsx`.
- [x] The report lists the monitored hosts (the lab owner chose: only monitored hosts). Proof: `TestReportAvailabilityMonitoredHosts`.
- [ ] Re-run TC-RPT-01 on the fixed build and record it in a new run report; keep the original failure. **Needs a person: the fixed build must be deployed to the lab first. Not done in this PR.**
- [ ] `scripts/verify.sh all` passes. On this Windows machine the gate has environment-only failures that are identical on clean main (see Decisions and notes); CI on Linux is the real check.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| State is "Unknown" on every row; expected real state | Item 1 | backend: status joined into availability rows; frontend: state text shown |
| Summary cards show Up 0 / Down 0 | Item 1 | backend: summary counts come from joined states |
| Last Check and Last State Change are blank | Item 1 | backend: ISO timestamps in rows; frontend: dates shown in the row |
| 13 rows against 9 monitored hosts (Missing devices and localhost listed) | Item 2 | backend: only hosts of monitored devices appear |
| Uptime % between 0 and 100 (already true, must stay) | Item 1 | `test_every_uptime_is_between_0_and_100` |
| Re-run TC-RPT-01 on a fixed build | Item 3 | lab run after deployment (a person) |
| Verification gate | Item 4 | `scripts/verify.sh all` (CI) |

## Plan

Precedent: `server/app/nagios/service_availability.py` already reads one archive plus at most one bulk status list and joins by full identity, with an explicit notice if current status fails. The host reports do the same with one `hostlist` read.

1. [x] Tests first (red): `server/tests/unit/test_host_current_status.py` (new), new classes in `server/tests/unit/test_report_availability.py`, `client/src/test/HostAvailabilityCurrentState.test.tsx` (new).
2. [x] New `server/app/nagios/host_current_status.py`.
3. [x] `server/app/api/system/report.py`: join status, `current_status` context, monitored-only rows for Host Availability.
4. [x] Frontend: `types/report.ts`, `HostAvailabilityReportTable.tsx`, `ReportsPage.tsx`, `ExtraReports.tsx`.
5. [x] Specs: `Backend_Modules_and_Routes.md`, `Frontend_Modules_and_Routes.md`, `Implementation_Status.md`; refreshed the `report.py` digest for TC-ROL-04 in `docs/qa/automation-coverage.json`.
6. [ ] Final gates and pull request.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Built on #217's code: backend, tests, frontend, specs (branch `issue-228-host-availability-state`) | pytest, vitest, tsc, lint, docs gate on an LF export | green apart from environment-only failures |
| 2 | #217 was reverted on main (#227), so the work was ported onto current main as `issue-228-host-current-state`: same module and tests, report.py and frontend re-applied to the older code, specs without the removed `Reports_Requirements.md` and manual | `pytest test_host_current_status.py test_report_availability.py` (29 passed); `vitest HostAvailabilityCurrentState + ServiceReports` (14 passed); 2 of 4 new frontend tests fail on main's source | green |

## State for the next session

- Last check run (exact command): `cd client && npx vitest run src/test/HostAvailabilityCurrentState.test.tsx src/test/ServiceReports.test.tsx`
- Result (first failing lines, or "green"): green (14 passed)
- Hypothesis: nothing open; remaining work is the full gates and opening the PR.
- Next action: run `tsc -b`, full vitest, lint, the docs gate on an LF export of this branch, then open the PR with `Closes #228`.

## Decisions and notes

- Base: the lab owner chose current `main` with #217. #217 was then reverted (#227), so this branch is rebuilt on the reverted main. The older branch `issue-228-host-availability-state` (based on #217) is abandoned and not used.
- Rows: only hosts of currently monitored devices (lab owner's choice). Consequence: a host that was monitored earlier in the period but is paused, retired or removed now is not listed.
- Hosts by OS shares the state/last-check join (same root cause) but keeps its own row set; filtering its rows is not in this issue.
- Live verification on the lab is out of scope here (needs a person to deploy).
- `docs/qa/automation-coverage.json`: only the `server/app/api/system/report.py` digest for TC-ROL-04 changed. A person should confirm that source review still holds (the 403 check on `/api/system/report/availability` is untouched; no permission decorator changed).
- Windows machine: backend pytest has 171 environment failures (tzset, file modes, symlinks, CRLF hashes) and the docs gate and frontend `node --test` fail on clean main too; the failing sets matched exactly between main and this work. A `python3 -X utf8` shim is needed for `scripts/*.sh`.
