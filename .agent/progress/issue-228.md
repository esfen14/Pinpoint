# Issue #228: TC-RPT-01: Host Availability report shows state Unknown, no last check, and unmonitored hosts

Branch: `issue-228-host-availability-state`
Status: in-progress
<!-- Status is one of: in-progress | blocked | ready-for-review -->

## Finish condition

Copied from the issue. Tick an item only when a check proves it.

- [ ] Each host row shows its real current state, last check and last state change from a real source, and the summary cards count Up and Down correctly. (The issue's alternative, changing the spec instead, was ruled out by the lab owner: "Show real data".)
- [ ] The report lists the monitored hosts (the lab owner chose: only monitored hosts).
- [ ] Re-run TC-RPT-01 on the fixed build and record it in a new run report; keep the original failure. **Needs a person: the fixed build must be deployed to the lab first. Not done in this PR.**
- [ ] `scripts/verify.sh all` passes.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| State is "Unknown" on every row; expected real state | Item 1 | backend test: status joined into availability rows; frontend test: state text and summary cards |
| Summary cards show Up 0 / Down 0 | Item 1 | backend test: summary counts come from joined states |
| Last Check and Last State Change are blank | Item 1 | backend test: ISO timestamps in rows; frontend test: table shows them |
| 13 rows against 9 monitored hosts (Missing devices and localhost listed) | Item 2 | backend test: only hosts of monitored devices appear |
| Uptime % between 0 and 100 (already true, must stay) | Item 1 | existing availability tests plus a range check |
| Re-run TC-RPT-01 on a fixed build | Item 3 | lab run after deployment (a person) |
| Verification gate | Item 4 | `scripts/verify.sh all` |

## Plan

Write the whole plan first. Precedent: `server/app/nagios/service_availability.py` already reads one archive plus at most one bulk status list and joins by full identity, with an explicit notice if current status fails ("no snapshot or live-status fallback" in Reports_Requirements §5 means no substitute for failed history; a bulk current-status read is the spec's own pattern for the service reports).

1. [ ] Tests first (red): `server/tests/unit/test_report_availability.py` and a new `server/tests/unit/test_host_current_status.py`: status join, ISO timestamps, summary counts, unavailable status notice with null state, pending host, monitored-only filter, hosts-by-os state.
2. [ ] New `server/app/nagios/host_current_status.py`: normalize one bulk `hostlist` read (details, enumerate) to `{host: {state, last_check, last_state_change}}`, reusing `request_cgi` and `AvailabilityError` from `service_availability.py`.
3. [ ] `server/app/api/system/report.py`: join current status into `/report/availability` and `/report/hosts-by-os` rows, add `current_status` {available, observed_at, notice}, and keep only hosts of monitored devices in `/report/availability` (via `monitoring_state`, `devices_by_host_name`).
4. [ ] Frontend: `client/src/components/reports/HostAvailabilityReportTable.tsx`, `client/src/types` and `ReportsPage.tsx`: show the notice when current status is unavailable, show state `—` for null; extend vitest tests.
5. [ ] Specs: `spec files/Backend_Modules_and_Routes.md`, `Frontend_Modules_and_Routes.md`, `Reports_Requirements.md` §3, `Implementation_Status.md`, `docs/manuals/Reports.md`.
6. [ ] `scripts/verify.sh backend`, `frontend`, `docs`, then `all`.

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Plan written; branch from origin/main 138d3a30; baseline `pytest tests/unit/test_report_availability.py` | pytest | 7 passed |

## State for the next session

- Last check run (exact command): `cd server && python -m pytest tests/unit/test_report_availability.py -q`
- Result (first failing lines, or "green"): green (7 passed, baseline)
- Hypothesis: `_availability_host` reads `state`, `last_check`, `last_state_change` from the archive availability row, which does not carry them; existing tests hid this by putting `"state": "UP"` in mocked rows.
- Next action: write the failing tests of plan step 1.

## Decisions and notes

- Base: current `main` with #217 (lab owner's choice). PR #227 (a revert of #217) is open; if it merges first, rebase and resolve.
- Rows: only hosts of currently monitored devices (lab owner's choice). Consequence to document: a host that was monitored earlier in the period but is paused, retired or removed now is not listed.
- Hosts by OS shares the state/last-check join (same root cause) but keeps its own row set; filtering its rows is not in this issue.
- Live verification on the lab is out of scope here (needs a person to deploy).
