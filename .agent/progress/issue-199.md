# Issue #199: Web-Interface Refinement Align Reports With Nagios Core Reporting and Revise the UI

Branch: `issue191-reports_alignment`
Status: in-progress

## Finish condition

The issue's 16 conditions, short form. Ticked items match the boxes ticked on the issue.

- [x] Cited native behavior mapped to each delivered feature; Pinpoint-specific choices identified
- [x] #198 contract intact; host/OS snapshot-count fields removed
- [x] All six existing views remain with shared period/scope/applied-query controls
- [x] Availability details: durations, both percentages, coverage, scheduled split
- [x] Exact-object timeline and interval table, reconciled with native totals
- [x] Alerts and Notifications filters/columns, totals, permission-safe History link
- [x] Alert Summary totals, distinct counts, deterministic ranking, drilldown
- [x] Alert Histogram: four breakdowns, zero buckets, zone/DST, drilldown
- [ ] UI states (insufficient history added), narrow layouts, focus, both themes verified in a browser
- [ ] CSV/XLS/PDF context verified by real browser downloads
- [ ] Native-shape API tests (removed objects, auth/timeout, multi-contact tests added; await review)
- [x] Instrumented limits/bounded-request tests and 24h/90d timings recorded
- [x] Reports spec, frontend/backend/data specs, routing and operator manual updated
- [ ] `scripts/verify.sh all` passes with output attached to the PR
- [ ] Lab report complete (maintenance and missing-history cases, export journeys)
- [ ] PR links the issue, CI green, human review

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Native behavior mapped; Pinpoint choices shown | item 1 | spec files/Reports_Requirements.md; About blocks |
| Snapshot counts removed from host/OS | item 2 | server/tests/unit/test_report_availability.py |
| Draft/applied query, stale runs, scope | item 3 | client/src/test/ReportsAnalysis.test.tsx, ServiceReports.test.tsx |
| Detail drawer and timeline | items 4, 5 | server/tests/unit/test_report_events.py; lab report |
| Alerts/Notifications filters | item 6 | test_report_events.py, ReportsAnalysis.test.tsx |
| Summary and Histogram | items 7, 8 | test_report_events.py; lab report |
| Limits and timings | item 12 | test_report_events.py (TestPaging); lab report |
| Docs | item 13 | verify.sh docs link checks |

## Plan

1. [x] Contract probe on the lab Nagios; sanitized fixture (server/tests/fixtures/archivejson_core_4_5_11.json)
2. [x] Reports requirements spec and routing (spec files/Reports_Requirements.md, AGENTS.md)
3. [x] Backend readers and routes (server/app/nagios/report_events.py, server/app/api/system/report.py)
4. [x] Frontend controls, drawer, analysis views, exports (client/src/pages/ReportsPage.tsx, client/src/components/reports/)
5. [x] Tests (server/tests/unit/test_report_events.py, client/src/test/ReportsAnalysis.test.tsx, ExportMeta.test.ts)
6. [x] Lab report (docs/test-runs/2026-10-18-issue-199-reports/REPORT.md)
7. [ ] Live scheduled-maintenance comparison; real export downloads; update the lab report
8. [ ] Delete this file before the PR is marked ready for review

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Host/OS durations, applied-query controls | pytest report tests, vitest | green |
| 2 | Backend readers/routes, drawer, analysis views, docs, lab report | pytest 4342 passed; vitest 1031 passed | green except existing environment failures |
| 3 | Layout simplification, insufficient-history state, failure/removed-object tests | vitest 1036 passed | green |
| 4 | Reverted unrelated Manage Accounts and dashboard edits; refreshed TC-ROL-04 report.py hash after impact review | `scripts/qa_coverage.py check` | 239 records validated |

## State for the next session

- Last check run (exact command): `scripts/verify.sh docs` with server/venv/bin first on PATH
- Result (first failing lines, or "green"): passes through the coverage-binding step; fails locally at test_qa_transport ("Unsafe transport path", macOS path) which is expected to pass on Linux CI
- Hypothesis: remaining QA-tooling failures are local-environment path issues, not caused by #199
- Next action: confirm CI is green, run the live maintenance comparison and real export downloads, then delete this file and mark the PR ready.

## Decisions and notes

- The Manage Accounts export fix and the dashboard "..." removal were taken out of this change because reviewed QA adapters (TC-ACC-08/10, TC-DASH-07) pin those files. They need their own change with the QA register reviewed.
- TC-ROL-04 pins server/app/api/system/report.py; its hash was refreshed after a source review that the 403 assertion on /report/availability still holds (decorators unchanged). Needs human confirmation.
- Open question for a person: History labels archive state type 2 as HARD; this Core sends HARD=1. Left unchanged here.
