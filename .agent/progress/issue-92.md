# Issue #92: Align Reports availability with Nagios source of truth

Branch: `issue-92-reports-nagios-availability`
Status: in-progress

## Finish condition

- [ ] `GET /api/system/report/availability` obtains availability from Nagios rather than calculating it directly from Pinpoint `HostStatus` snapshots.
- [ ] `GET /api/system/report/hosts-by-os` uses the same Nagios-backed availability source and semantics.
- [ ] The selected reporting period and host scope are passed to Nagios correctly.
- [ ] The Reports API response remains compatible with the existing frontend, or any intentional response change is documented and tested.
- [ ] Network Health and Reports produce equivalent availability values for equivalent hosts, windows, and calculation options, subject only to documented rounding.
- [ ] Nagios request failure and no-data cases return clear, tested error or unavailable responses without silent snapshot fallback.
- [ ] Backend tests cover Nagios-backed results, period handling, hosts-by-os grouping, no-data behavior, request failure, and prevention of snapshot fallback.
- [ ] Frontend tests and build pass.
- [ ] Relevant route and implementation documentation describe Nagios as the availability authority.
- [ ] A sanitized test report records observed results and remaining limitations.
- [ ] `scripts/verify.sh all` passes.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Reports availability uses Nagios | 1 | Backend availability route tests |
| Hosts-by-OS uses same Nagios semantics | 2 | Backend hosts-by-os tests |
| Period and host scope reach Nagios | 3 | Mock call argument tests |
| Existing frontend contract remains compatible | 4 | Backend response tests; frontend tests/build |
| Equivalent Network Health/Reports values | 5 | Shared helper/aggregation tests |
| Failure/no-data is explicit; no snapshot fallback | 6 | Failure, empty, and snapshot-populated tests |
| Backend coverage listed | 7 | Targeted pytest and verify backend |
| Frontend tests/build | 8 | verify frontend |
| Documentation | 9 | Docs diff and verify docs |
| Sanitized test report | 10 | Committed docs/test-runs report |
| Full verification | 11 | scripts/verify.sh all |

## Plan

1. [ ] Step: Add failing backend tests for Nagios-backed availability, period/host forwarding, hosts-by-OS grouping, no-data/failure, and snapshot fallback prevention in `server/tests/unit/test_report_availability.py`.
2. [ ] Step: Implement shared Nagios availability querying and compatible response aggregation in `server/app/nagios/notifications.py` and `server/app/api/system/report.py`.
3. [ ] Step: Run targeted backend tests, then backend verification; record results in this file.
4. [ ] Step: Update route/catalog/status documentation to describe Nagios authority in `spec files/Backend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, `spec files/Implementation_Status.md`, and the frontend report description in `client/src/pages/ReportsPage.tsx` if needed.
5. [ ] Step: Run frontend verification and create a sanitized issue test report in `docs/test-runs/2026-10-11-issue-92/REPORT.md` plus its index row.
6. [ ] Step: Re-read issue, run `scripts/verify.sh all`, tick proven finish conditions, remove this progress file, commit, push, and open the pull request.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Added failing Nagios-source tests, implemented archivejson-backed availability for both report routes, forwarded optional hostname scope, and updated an existing stable-name test to mock Nagios. | `server/.venv/bin/python -m pytest server/tests/unit/test_report_availability.py server/tests/unit/test_device_name_consumers.py::TestReportUsesTheNagiosName -q` | 7 passed; initial test-first run failed because the helper was not yet imported, then implementation passed. |
| 2 | Updated route/data/status documentation and Reports description; verified targeted report/consumer/alert tests and docs. | `scripts/verify.sh docs`; `cd server && .venv/bin/python -m pytest tests/unit/test_report_availability.py tests/unit/test_report_notifications_alerts.py tests/unit/test_device_name_consumers.py -q`; `scripts/verify.sh backend` | Docs green; targeted backend 58 passed. Full backend reached pytest with route drift green but exceeded the 120-second command timeout while still running; no test failure observed. |

## State for the next session

- Last check run (exact command): `server/.venv/bin/python -m pytest server/tests/unit/test_report_availability.py server/tests/unit/test_device_name_consumers.py::TestReportUsesTheNagiosName -q`
- Result (first failing lines, or "green"): green, 7 passed
- Hypothesis: Reports now uses the same Nagios archive availability source as Network Health and does not read HostStatus for these endpoints.
- Next action (one specific step, not "continue"): clean up route documentation and run the broader backend verification, then update the owning specifications and test-run report.

## Decisions and notes

- Issue finish condition has explicit coverage for every stated requirement; no clarification needed.
- Existing migration deletions/untracked migration from the starting worktree were present after branch checkout and are preserved as unrelated user changes.
