# Test run: issue-199-reports

| | |
|---|---|
| Date | 2026-10-18 |
| Commit tested | Base `39ac83e5` plus the uncommitted #199 working tree (Reports requirements, `report_events.py`, new routes, drawer, analysis views, export context); the final commit is recorded in the PR |
| Plan | GitHub [#199](https://github.com/esfen14/Pinpoint/issues/199), phases 1-5 of the saved plan |
| Tester / executor mode | AI-assisted (Claude) on the owner's machine; no human review yet |
| Catalog revision and SHA-256 | Not applicable (not a QA-catalog run) |
| Queue / set / session / batch | None |
| Deployed application / installer revision | Docker lab appliance built from the working tree with `scripts/lab sync`; no installer-built appliance |
| Baseline / preflight / restoration | Lab database deleted and rebuilt (`flask db upgrade` + seed) because the old container database lacked a newer migration; `scripts/lab smoke` 9/9 before testing. The one induced outage (`web01`) was ended with `scripts/lab fix web01 all`; no other lab object changed |
| Start / end / time zone | About 20:00 to 21:10, server time zone UTC (container), display zone from the user's settings |
| Environment | macOS host, Docker lab (Nagios Core 4.5.11, 6 hosts: localhost, web01, web02, app01, snmp01, legacy01), Vite dev UI on 127.0.0.1:5173, in-app Chromium. The lab's Nagios had been restarted shortly before, so its history is short |
| Raw evidence | Host-local `/tmp/probe/*.sh` probe scripts and the lab container; never committed. A sanitized capture is `server/tests/fixtures/archivejson_core_4_5_11.json` |

## Result

**Overall: Partial.** The archive contract was probed on a real Core 4.5.11, the new
endpoints and UI were exercised against real lab data, and host durations matched the
native `avail.cgi` report for identical bounds. Scheduled-maintenance breakdown, scale
beyond six hosts, real-browser file downloads of each export format and an
installer-built appliance were not tested.

Totals (this run's own cases): Pass 10, Fail 0, Partial 1, Not run 3.
Historical credit: none. These are not QA-catalog cases.

## Cases

| Case | Result | Notes (what was observed) | Issue |
|---|---|---|---|
| R199-PROBE | Pass | Read-only probe of `archivejson.cgi`: queries, `start`/`count` paging, millisecond timestamps, bitmask states, initial pseudo-state entry, single `host`/`service` object for exact availability, `type_code 6` for a reversed range, unknown object = success with no object. Recorded in Reports_Requirements | — |
| R199-STATE-TYPE | Pass | Induced a real `web01` outage: log showed SOFT 1, SOFT 2, HARD 3; the archive `statetypes=hard` filter returned only the third and its `state_type` was 1. So HARD=1, SOFT=2. The previous normalizer assumed the reverse (see Findings) | — |
| R199-HOST-PARITY | Pass | Same bounds (1792241583 to 1792327983) for `web01`. Native `avail.cgi` CSV: up 182 s, down 655 s, 0.211% / 0.758% of total, 21.744% / 78.256% of known, not running 69841 s, no data 15722 s. Pinpoint detail: up 182, down 655, 0.21% / 0.76%, 21.74% / 78.26%, no recorded data 85563 s (= 69841 + 15722). Percentages differ only by rounding (2 vs 3 decimals) | — |
| R199-OUTAGE-TIMELINE | Pass | Brief outage (655 s down, then recovery): intervals `no_data` (unknown onset), `down` 655 s, `up` (continuing); reconciliation matched with no differences | — |
| R199-SERVICE-DETAIL | Pass | `localhost`/SSH over 7 days: critical 7533 s native; the event timeline continued through 597235 s of Nagios downtime, so it reconciled against the downtime-carried native answer and the drawer states the downtime seconds | — |
| R199-DISCREPANCY | Pass | `localhost` host over 7 days: native counted 604800 s Unreachable from retained state with no archive event. Intervals were withheld with a notice and per-state differences instead of being invented | — |
| R199-SUMMARY | Pass | Alert Summary on real events: policy line, 2 problem events, 2 distinct hosts, recoveries separate; ranking by count then host/service | — |
| R199-HISTOGRAM | Pass | 96 hour slots and 7 weekday buckets, zero buckets kept; the one HARD event landed in the 15:15 slot (server zone UTC; the table shows the user's display zone) | — |
| R199-DRILLDOWN | Pass | "Open alerts" on a summary row opened Alerts for that host/service with the same period; the list showed HARD and SOFT rows with the State Type column | — |
| R199-UI-DRAWER | Pass | Drawer in the in-app browser, light and dark: duration bar with text legend, table with both percentages, coverage, History link (admin has `system.history`) | — |
| R199-NARROW | Partial | Controls wrap at tablet width. Below 768 px the whole app shell (fixed sidebar) overflows horizontally; this predates #199 and is not specific to Reports | not filed |
| R199-MAINTENANCE | Not run | No scheduled downtime was created in the lab, so the scheduled/unscheduled split was verified only with native-shape unit fixtures | — |
| R199-EXPORT-DOWNLOAD | Not run | CSV/XLS/PDF context lines and HTML escaping are covered by unit tests against the real export module; a real browser download of each format was not performed | — |
| R199-SCALE | Not run | Only the 6-host lab; limits are enforced and unit-tested, not load-tested | — |

## Timings (lab, 6 hosts, a handful of events)

| Request | Last 24 h | Last 90 d |
|---|---|---|
| availability-detail (host) | 21 ms | 24 ms |
| alert-summary | 11 ms | 12 ms |
| alert-histogram | 11 ms | 12 ms |
| alerts | 16 ms | 18 ms |
| availability | 11 ms | 12 ms |

These say nothing about large installs. The code bounds each report to 45 archive
requests, 20,000 events and 30 seconds, then returns `complete: false`.

## Automated checks

Local, with `server/venv/bin` first on `PATH`: backend 4342 passed, 26 skipped, 5 failed
(4 `test_ssh_port.py` failures also occur without these changes: the test uses a macOS-incompatible `sed`;
1 `test_history.py` failure was caused by an earlier version of this change and fixed, targeted rerun of
history, report-events and report-alert tests: 231 passed); route catalog and client API drift checks pass;
frontend 1031 passed, `eslint` 0 errors (36 warnings), `vite build` passes. `scripts/verify.sh docs` passes
every step except the existing `test_qa_transport` ("Unsafe transport path"), and `verify.sh frontend`
type-checking fails only on the Playwright e2e files (`@playwright/test` is not installed). The
complete backend suite was not rerun after the History fix.
New tests: `server/tests/unit/test_report_events.py` (49), `client/src/test/ReportsAnalysis.test.tsx`
(15) and `client/src/test/ExportMeta.test.ts` (4), plus changed host-report and Reports page tests.

## Findings

1. **HARD/SOFT are reversed in the shared alert normalizer.** `normalize_alert`
   treats `state_type == 2` as HARD; on this Core HARD is 1. Reports now use the probed
   mapping (`REPORT_HARD_STATE_TYPE`). The **History** page still uses the legacy
   mapping, because #199 must not change History contracts; its
   `test_real_nagios_alert_shape` encodes the old assumption. A person should decide
   whether to fix History in its own issue.
2. **Single-host availability returned 502.** With `hostname` the CGI answers with a
   `host` object, but `request_host_availability_range` read `hosts`. Fixed.
3. **Host reports now send explicit assumptions** (no assumed initial state, state
   not assumed during Nagios downtime), matching the service reports. Core's defaults
   assume both, so host numbers can differ slightly from before when Nagios was down
   or history is short.
4. The lab's `alertcount` response key is `count`, not `alertcount`, so the existing
   alert count helpers always return `None`; the Alerts card totals come from the rows.
   Left unchanged.
