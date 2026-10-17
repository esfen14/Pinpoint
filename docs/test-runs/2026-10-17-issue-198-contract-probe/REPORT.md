# Issue #198: installed service-availability contract probe

Result: **Blocked before implementation** on the contract decision in
[issue #198](https://github.com/esfen14/Pinpoint/issues/198).
This is a read-only contract probe, not the final two-view acceptance report.

## Environment and exact source

- Repository commit tested/inspected: `8cf01ab75ae407291d75b884de2455c6c49b0ee2` (issue plan commit;
  product source unchanged from main `44d80180`).
- Installed Nagios binary: **Core 4.5.11**, observed using `nagios --version`.
- Existing VM lab explicitly reserved by the owner for this work. Ownership
  preflight passed with VM UUID `351eb491-f5e1-4854-a7e4-68309ad774ad`.
- VM was powered off, started using `scripts/vmlab up`; no reset, restore,
  monitoring-config change, service fault or deployment occurred.
- CGI executed read-only as the existing `www-data` user with the existing
  CGI authorization identity. No passwords or raw logs were captured.
- Inventory returned: eight configured services on one host (stock localhost).
  This is not the five-target lab inventory required for final acceptance.
- Upstream source inspected:
  [official Core 4.5.11 archivejson.c](https://github.com/NagiosEnterprises/nagioscore/blob/nagios-4.5.11/cgi/archivejson.c),
  `compute_window_availability` and `compute_service_availability`.

## Options and windows

`query=availability`, `availabilityobjecttype=services`, `statetypes=hard`,
`assumeinitialstate=false`, `assumestateretention=true`,
`assumestatesduringnagiosdowntime=false`, `backtrackedarchives=4`.
The echoed response selector uses the singular spelling
`assumestateduringnagiosdowntime`, unlike the request parameter.
Request timestamps are Unix **seconds**; echoed timestamp fields are integer
**milliseconds**. Duration fields are nonnegative integer **seconds**.
Envelope success is `result.type_code=0`, `type_text=Success`.

Fixed-window capture:

| Case | Exact start/end (Unix seconds) | CGI wall time | CGI output size | Result |
|---|---|---:|---:|---|
| 24h | 1792159056 / 1792245456 | 0.0027 s | 4170 bytes | Native shape pass; every duration zero |
| 90d | 1784469456 / 1792245456 | 0.0037 s | 4170 bytes | Native shape pass; every duration zero |
| Missing history | 978307200 / 978393600 | 0.1372 s | 4156 bytes | Eight rows, all durations zero, including indeterminate fields |
| Absent host | 1792159056 / 1792245456 | 0.0022 s | 867 bytes | Success with `data.services=[]` |
| Host+service selectors | 1792159056 / 1792245456 | 0.0019 s | 1278 bytes | Success with `data.service` object |

Query times were 1792245479/80. Sizes include CGI headers, not HTTP headers or
a Pinpoint report response. These are single-run CGI timings only; they do not
establish request latency through HTTP, API, browser, or large-scale capacity.

## Cases and findings

| Case | Outcome | Evidence / implication |
|---|---|---|
| Native shapes, envelope and units | Pass | Sanitized fixtures under `server/tests/fixtures/nagios_service_availability/`; full identity pair in each native row |
| Empty versus no history | Pass for observed distinction | Empty selector gives no rows; missing history gives configured rows with all-zero durations |
| Scheduled maintenance inclusion | Blocked: #198 decision | Source inspection shows scheduled states accumulate into `scheduled_time_*` instead of `time_*`; normalized state seconds must add both to satisfy maintenance inclusion |
| Complete missing coverage under the approved formula | Blocked: #198 decision | In the missing-history fixture, `no_data + notrunning` is zero for a full 86400-second range; this would misleadingly show zero known and zero missing time |
| Initial state / fixed historical windows | Blocked: #198 investigation | Preliminary live-now probe and fixed-window rerun differed dramatically; details below. Cannot declare strict recorded-time semantics supported yet |
| Bulk status, HTTP auth, errors, timeout and credentials | Skipped | CGI-only probe; no adapter or route implementation yet |
| Brief outage, bounds, downtime and native avail.cgi comparison | Skipped | No fault injected, no monitoring configuration changed; final acceptance pending |
| Two report views, API/UI/exports and full verification | Skipped | Implementation intentionally not started while contract assumptions are unresolved |

An initial live-now query ending at its current Unix second returned 547 OK /
85853 engine-down seconds for 24h and 7601076 OK / 174924 engine-down seconds
for 90d. The fixed-window rerun ending at 1792245456 returned all zeros only
23 seconds later, using identical options and configured objects. A second
live-now diagnostic using `assumestateretention=false` also returned 7601076 OK /
174924 engine-down seconds for 90d, while a second fixed-window query returned
zeros. These results were observed in tool output; only the fixed-window native
responses were saved as fixtures. This is a contract warning, not a product
failure or a claim of measured 90-day uptime. Core source includes a current
pseudo-state path when there is no state history and the query window includes
query time, independently of `assumeinitialstate`. Exact causal attribution
still needs investigation before choosing a design.

## Concrete corrections proposed for owner decision

1. Normalize each observed state as `native time_STATE + scheduled_time_STATE`;
   compute headline availability from the four normalized totals. Preserve
   scheduled component fields so maintenance is transparent and never subtracted.
2. Preserve native indeterminate components and add explicit
   `unaccounted_seconds = window_seconds - sum(all native state, scheduled state,
   and indeterminate durations)` when nonnegative. Show this as missing coverage,
   separately identified from native “no data” and engine downtime. Reject sums
   exceeding the window. This changes the proposal's two-component coverage formula.
3. Keep implementation blocked until the no-history/current-state synthesis and
   fixed-window discrepancy have a demonstrated solution that satisfies strict
   recorded-time semantics. Do not silently accept pseudo-state estimates or
   introduce a database fallback. Any different source/extra upstream requests or
   Core change needs an explicit scope decision.

The issue itself requires resolving disproven assumptions before implementation.
No acceptance item has been marked complete based on this partial probe.
