# Test run: issue-134-reports-documentation

| | |
|---|---|
| Date | 2026-10-17 |
| Commit tested | `65101a5f876a8a5d9894dd59ecdeb47a23a8dad6` plus documentation-only corrections described below; application source unchanged from `4b1ad9f5` |
| Plan | GitHub [#134](https://github.com/esfen14/Pinpoint/issues/134), Part 21.1; user explicitly rejected Parts 21.2/21.3 |
| Tester | Codex |
| Environment | Linux 6.12.105, Python 3.14.6, Node 20.19.2; isolated backend fixtures and copied frontend dependencies in the issue worktree; live appliance Nagios Core 4.5.11, headless Chromium via Playwright |
| Raw evidence | Host-local `/tmp/issue-134-resume-docs.log`, `/tmp/issue-134-resume-all.log`, `/tmp/issue-134-browser-final.log`, `/tmp/issue-134-browser-results.json`, `/tmp/issue-134-readonly-reports.py`, `/tmp/issue-134-reports-browser.cjs`, `/tmp/issue-134-live-api.log`, `/tmp/issue-134-appliance-version.log`; never committed |

## Result

**Overall: Pass for the documentation reconciliation scope.** The source audit, docs checks,
full verification gate, all six populated report views and all six CSV exports passed. The browser
checks used the existing appliance at `82ba9ce9aefda8fbbad93ba500a9cacf23c56409`;
its seven relevant tracked report source files match this branch byte-for-byte,
and its tracked worktree is clean (only an unrelated untracked npm cache exists).
No deployment or guest source edits were needed. Runtime browser output is in
`issue-134-browser-final.log`.

Totals: Pass 8, Fail 0, Blocked 0, Skipped 0. Each UI case includes a view check and a CSV export check. Backend skips are reported separately above.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| R134-DOCS | Pass | `scripts/verify.sh docs` exited 0; `issue-134-resume-docs.log` | — |
| R134-ALL | Pass | `scripts/verify.sh all` exited 0: 3991 backend passed / 14 skipped; 73 frontend files / 912 tests passed; build passed; lint 0 errors / 31 warnings; final line `verify: all OK` | — |
| R134-UI-AVAILABILITY | Pass | Playwright opened Host Availability, received HTTP 200, checked its heading and populated table (6 visible rows); downloaded CSV and asserted exact documented column names and nonempty content | — |
| R134-UI-NETWORK-SERVICES | Pass | Playwright opened Network Services, received HTTP 200, checked its heading and populated table (8 visible rows); downloaded CSV and asserted exact documented column names and nonempty content | — |
| R134-UI-HOSTS-BY-OS | Pass | Playwright opened Hosts by OS, received HTTP 200, checked its heading and populated table (6 visible rows); downloaded CSV and asserted exact documented column names and nonempty content | — |
| R134-UI-DEVICE-SERVICES | Pass | Playwright opened Device Services, received HTTP 200, checked its heading and populated table (8 visible rows); downloaded CSV and asserted exact documented column names and nonempty content | — |
| R134-UI-ALERTS | Pass | Playwright opened Alerts, received HTTP 200, checked its heading and populated table (10 visible rows); downloaded CSV and asserted exact documented column names and nonempty content | — |
| R134-UI-NOTIFICATIONS | Pass | Playwright opened Notifications, received HTTP 200, checked its heading and populated table (10 visible rows); downloaded CSV and asserted exact documented column names and nonempty content | — |

## Source audit (inspection, not runtime evidence)

The Reports section of
[Frontend modules and routes](../../../spec%20files/Frontend_Modules_and_Routes.md#reports)
records all displayed columns, summary cards, period handling, filters and export
columns. All six API routes are listed there and match the route decorators.

| View | GET route | Component inspected |
|---|---|---|
| Host Availability | `/api/system/report/availability` | ReportsPage and HostAvailabilityReportTable |
| Network Services | `/api/system/report/network-services` | ReportsPage and NetworkServicesReportTable |
| Hosts by OS | `/api/system/report/hosts-by-os` | ExtraReports |
| Device Services | `/api/system/report/device-services` | ExtraReports |
| Alerts | `/api/system/report/alerts` | ExtraReports |
| Notifications | `/api/system/report/notifications` | ExtraReports |

Inspected `server/app/api/system/report.py`, report types, `ExportMenu` and
`exportData.ts` against those components. Verified by an assertion-based source
cross-check that the six labels/routes and all six period values are documented.
The Network Services export heading is `Total Instances` (the on-screen heading
is `Instances`); the documentation now preserves that distinction. Host exports
retain the existing legacy `Total Snapshots` heading whose value is known-state
seconds; removal/redesign is tracked in #199. Service snapshot-count removal
and Nagios duration sourcing are tracked separately in #198. No product defect
was fixed or new report implemented by this documentation change.

## Deviations from the plan

- Availability targets, target settings/migrations/indicators, associated tests
  and Help changes were rejected by the owner; no application code changes were
  needed. Backend/data specifications and Display Requirements were inspected;
  the existing route catalog/source ownership remains unchanged, so those files
  do not need unrelated edits.
- No new tests mirror prose changes. Existing isolated suites and drift checks
  provide regression coverage; they do not replace the six-view browser check.
- The earlier full gate ran under filesystem/network restrictions and reported
  five failures plus one error from denied socket creation/DNS (3985 backend
  passes, 14 skips). The resumed run uses the current unrestricted environment.
- The computer-use tool had no connected browser, so the owner explicitly
  authorized Playwright. The first login attempts used a config override state
  directory rather than the directory resolved by the actual lab helper; those
  returned 401. Using the helper's real state directory succeeded without any
  account or credential change. An expired stored browser session was not used.
- The initial browser harness passed five views but its Notifications selector
  also matched the header bell. After diagnosing the strict locator error, the
  harness selected the text-bearing report tab; the complete repeat passed all
  six views and exports. This was a harness error, not a product failure.
- Playwright used the Last 90 days period to include retained lab data. Alerts
  and Notifications each had more than ten records; paging limited visible rows
  to ten. API-only cross-checks also returned HTTP 200 for all six endpoints.
- No credentials, login screenshots, traces or videos were captured. Appliance
  startup used the ownership guard; no sync, redeployment, restore, discovery or
  target manipulation was performed. Existing source was preserved. The guarded shutdown returned the appliance
  to its initial powered-off state with ownership preflight passing.
- XLS and PDF export controls/implementations and all period values were inspected
  in source; actual downloads/printing in those two formats and interactive
  custom-date entry were not exercised. No such runtime pass is claimed.

## Follow-up

- Keep #198 (service source) and #199 (reporting/UI revision) as separate work.
- Reviewer approvals and green remote CI must be observed separately.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
