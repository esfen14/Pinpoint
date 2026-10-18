# Issue #198: service availability implementation and native comparison

Result: **Corrected implementation passes local and scoped live acceptance.**
An earlier harness isolation failure and its recovery are retained below. Remote
CI and human review are separate gates; see [PR #201](https://github.com/esfen14/Pinpoint/pull/201).

## Exact source and environment

- Final live/API/browser source: `3554f12357259f9c7a5947d84a8394f56068e487`.
  Tracked server files were exported with `git archive`; client assets were built
  from that checkout. No product source changed after this comparison.
- Installed binary version observed by the harness: **Nagios Core 4.5.11**.
  Appliance Python: installed `/opt/pinpoint/venv/bin/python`; browser: local
  headless Chromium through the repository's pinned Playwright package.
- Owner explicitly reserved the existing VM exclusively. Ownership preflight
  passed for UUID `351eb491-f5e1-4854-a7e4-68309ad774ad`.
- Live checks used a **separate Core process** with temporary config, logs,
  check results, status, query socket and databases. It checked a local fixture
  file, with one host and one service. All notifications were disabled and the
  dummy contact had a no-delivery command. No device scans, destructive reset,
  live monitoring-configuration edit, production database migration or app
  deployment occurred. The browser used a temporary loopback fixture login;
  production login/permission enforcement is covered separately by API tests.
- HTTP loopback adapters execute the installed archive/status CGI binaries with
  the fixture's CGI config. Native `avail.cgi` CSV is invoked directly with the
  same window and equivalent assumptions. This does not test installer/Nginx
  authentication or production reverse-proxy behavior.
- Raw synthetic-Core config/status/logs retained privately on the appliance at
  `/tmp/issue198-evidence-final`; host-local outputs are
  `/tmp/issue-198-final-live.log`, `/tmp/issue-198-final-browser.log`,
  `/tmp/issue-198-all.log`, `/tmp/issue-198-final-focused.log` and
  `/tmp/issue-198-final-frontend.log`. Raw evidence is not committed.

## Options and exact comparison

Archive options: `availabilityobjecttype=services`, `statetypes=hard`,
`assumeinitialstate=false`, `assumestateretention=true`,
`assumestatesduringnagiosdowntime=false`, `backtrackedarchives=4`.
Native availability options: `assumeinitialstates=no`,
`assumestateretention=yes`, `assumestatesduringnotrunning=no`,
`includesoftstates=no`, `backtrack=4`; no restricted reporting timeperiod.

The final observed window was **1792248159–1792248168 Unix seconds**, end exclusive.
The real check first returned OK, then CRITICAL, then OK. The recorded outage
lasted **4 seconds**, below Pinpoint's minimum 30-second polling interval.
The fixture Pinpoint poller was disabled; historical data came from Nagios logs.

| Source/view | OK seconds | CRITICAL seconds | Known seconds | Missing seconds | Availability during recorded time |
|---|---:|---:|---:|---:|---:|
| Native archivejson, normalized | 5 | 4 | 9 | 0 | 55.56% |
| Native avail.cgi CSV | 5 | 4 | 9 | 0 | 55.556% (native three-decimal output) |
| Network Services API and browser | 5 | 4 | 9 | 0 | 55.56% |
| Device Services API and browser | 5 | 4 | 9 | 0 | 55.56% |

The harness fixes only its custom comparison window after calling normal period
validation, allowing both views to query exactly the same brief outage. Browser
custom-date entry tests therefore prove controls/request/rendering, while the
unmodified API period resolver's inclusive date/timezone/DST behavior is proven
by the isolated API regressions. Current status was independently OK after
recovery, rather than inferred from the historical percentage.

For 2001-01-01 (978307200–978393600), both APIs returned null availability,
zero known seconds and **86400 missing seconds**, matching native avail.cgi.
In this live fixture Core categorized that missing range as engine-not-running;
the earlier installed no-history fixtures instead returned all-zero native
fields. Both are handled without inventing healthy time or a database fallback.

## Cases

| Case | Result | Evidence |
|---|---|---|
| Native response shapes and strict failure semantics | Pass | `test_service_availability.py`: list/single/empty, envelopes, finite/nonnegative numbers, duplicates, excess durations, timestamps and sanitized errors |
| Scheduled maintenance, UNKNOWN, engine downtime, initial/boundary states | Pass | `recorded-transitions.json` captured from installed CGI over separate supplied logs; 720 OK / 130 CRITICAL / 50 UNKNOWN / 100 engine-down seconds; 80% of 900 recorded seconds; OK before and exactly at start, WARNING exactly at exclusive end |
| Zero-known and partially missing coverage | Pass | Native missing-history fixtures, helper tests, API/browser cases; unaccounted remainder remains distinct from native components |
| Duration source, full identity and weighted aggregation | Pass | API tests seed conflicting all-OK snapshots for the same instance and a DB-only service; native results remain unchanged. Unequal durations and zero-known instances verify weighted raw-second sums and identical rows in both reports |
| Current versus historical context | Pass | Bulk status join/pending/missing/failure tests; browser shows current observation separately from 55.56% historical availability |
| Login and system.report permission | Pass | Direct unauthenticated and limited-role API tests for both routes |
| Request count and timeout budget | Pass | Instrumented 300-host mocked routes use one archive and one status call. Empty uses one archive only. Remaining-budget/exhaustion tests enforce the 10-second per-call / shared 20-second timeout allocation |
| Real brief recorded outage and native availability | Pass | Final table above; both APIs and Chromium views match the same native duration window |
| Real missing-history comparison | Pass | Both views match native missing coverage, without synthetic DB rows |
| Search, state filter, sorting and ten-row paging | Pass | `ServiceReports.test.tsx` with twelve-row tables; export covers all filtered rows, not only the current page |
| Custom dates and display zones | Pass | API UTC/Kathmandu/New York DST regressions (24h/23h/25h inclusive days), offset-bearing metadata; browser custom inputs and Run Report |
| Failed and invalid reruns; loading/empty/null | Pass | Interaction regressions clear prior service rows and hide export until success; no stale range can be exported after failure |
| CSV/XLS/PDF | Pass | Unit interactions invoke the real serializer for both tables; final Chromium run downloads CSV/XLS and produces PDF bytes from each print view; no snapshot labels/fields and explicit seconds/current headings |
| Host/OS and alert/notification regressions | Pass | Focused existing report tests and full isolated suite; host legacy export/count label preserved |
| Initial harness query-socket isolation | **Fail, corrected — [#198](https://github.com/esfen14/Pinpoint/issues/198)** | Early standalone Core configs omitted query_socket, so Core used/unlinked the main daemon's default socket at teardown. The main daemon remained active. This was a harness failure, not product evidence |
| Main socket recovery and corrected isolation repeat | Pass | Guarded main Nagios restart restored the socket; service active and main/localhost config digests unchanged. Corrected harness sets temporary query_socket/debug_file, disables syslog, and asserts the original main socket inode is unchanged on cleanup |
| Final isolated fixture cleanup | Pass | After browser checks the owned fixture was intentionally stopped with SIGINT; its finally block stopped the private Core, asserted main socket preservation and saved raw evidence. The logged KeyboardInterrupt/SSH nonzero termination is the requested fixture stop, not a failed product assertion. Main Nagios remained active with its query socket present |

The earlier live-only run also passed a six-second CRITICAL outage (6 OK / 6
CRITICAL seconds, 50%) against native avail.cgi. An initial harness config lacked
Core's required contact; a no-delivery contact corrected that setup error.
Another harness assertion incorrectly required all missing time to be unaccounted;
it was corrected to total missing coverage, preserving the native components.
No product defect was filed for either harness assumption, and no failing product
case was relabeled as a pass.

## Measured performance and limits

One host / one service in a fresh isolated Core. The elapsed figures below are
Flask test-client route times including real loopback HTTP/CGI execution; sizes
are complete serialized API response bytes. These are single small-inventory
measurements, not load-test percentiles or production network capacity claims.

| View | Window | Elapsed | API bytes | Known seconds | Missing seconds |
|---|---|---:|---:|---:|---:|
| network-services | last_24h | 0.006706 s | 1896 | 12 | 86388 |
| network-services | last_90d | 0.007185 s | 1914 | 12 | 7775988 |
| device-services | last_24h | 0.007977 s | 1902 | 12 | 86388 |
| device-services | last_90d | 0.008117 s | 1920 | 12 | 7775988 |

Each measured route made one archive and one status request. The final native
archive bodies were 1068 bytes for 24h and 1070 bytes for 90d; current status body
was 2025 bytes. The separate installed stock-inventory probe covered one host /
eight services, but was CGI-only. Instrumentation at 300 hosts is mocked, not
real capacity evidence. No cache or large-scale performance claim is introduced.
The timeout allocation does not claim a hard whole-response deadline for an
upstream that continuously streams bytes.

## Verification output

Observed full local gate, `/tmp/issue-198-all.log`:

```text
4040 passed, 14 skipped in 461.78s (0:07:41)
Test Files  74 passed (74)
Tests       922 passed (922)
verify: all OK
```

The final supplementary helper/API tests include the two timeout-budget cases
added after that suite's collection: **51 passed in 4.21s**. A final frontend
stage after wording/scope corrections passed all tests, build and lint.
Final browser run on the commit above: **2 passed (2.3s)**, covering both views
and all three export formats. Existing lint reports 31 warnings and zero errors;
Vite retains its existing bundle-size warning. Fourteen backend platform/live
skips remain; no tests were removed, weakened or newly skipped.

## Requirements and exclusions

The backend/data/frontend/status specifications and
[operator guide](../../manuals/Service_Reports.md) document sources, formulas,
removed snapshot-count fields, seconds, coverage, completed-second bounds,
current status and retention limits. The owner approved the scheduled-component
and unaccounted-coverage corrections after reviewing the initial probe.
Stored snapshots/general polling remain unchanged. No targets, permission,
dependency, migration, recurring email, scheduler or host-report redesign was
added. Native archive retention still limits what can be reported, and removed
configured objects may be absent. Installer upgrade/deployment, production HTTP
authentication and large real inventories were not exercised in this run.
