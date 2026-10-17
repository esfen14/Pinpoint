# Service reports from Nagios availability

Status: approved for an implementation issue by the owner on 2026-10-17;
application implementation has not started.

Context: GitHub [#134](https://github.com/esfen14/Pinpoint/issues/134), which
originally reconciles report documentation and conditionally proposes targets.
The owner rejected availability targets and subsequently requested a plan for
moving the two database-backed service reports to Nagios. This is a separate
follow-up scope; do not represent it as already implemented or close #134 on the
strength of this plan. Track implementation in the linked issue with the finish
conditions below.

Feeds these owning specifications when implemented:

- [Backend modules and routes](../../spec%20files/Backend_Modules_and_Routes.md), report route catalog.
- [Data model and integrations](../../spec%20files/Data_Model_and_Integrations.md), current state versus durable history and aggregation rules.
- [Frontend modules and routes](../../spec%20files/Frontend_Modules_and_Routes.md), Reports.
- [Implementation status](../../spec%20files/Implementation_Status.md), report data sources and verification limits.

## Recommendation and reason

Use Nagios archive availability as the source of measured service uptime for
both Network Services and Device Services. Fetch it when a report runs or its
period changes. This is a request for a historical range, not a new scheduler
job or a faster status-polling loop.

Pinpoint currently computes OK snapshot count / total snapshot count. Snapshots
can miss transitions between collection runs, and counting checks gives each
check equal weight even if checks were irregularly spaced. Nagios computes time
in each state from its recorded history. That better answers how much of the
selected period the service was available. Its accuracy still depends on what
Nagios checked and retained; it cannot recover unobserved outages or deleted logs.

## Current implementation inspected

| View | Route | Existing source and grouping |
|---|---|---|
| Network Services | `GET /api/system/report/network-services` | `ServiceStatus` rows in the selected window, grouped by service description across hosts; summary and state counts use each instance's latest check within that window |
| Device Services | `GET /api/system/report/device-services` | The same snapshot calculation, grouped by hostname; each row is a host/service pair and includes a snapshot count |

Relevant source: `server/app/api/system/report.py`,
`server/app/nagios/notifications.py`, `client/src/types/report.ts`,
`client/src/pages/ReportsPage.tsx`,
`client/src/components/reports/NetworkServicesReportTable.tsx`,
`client/src/components/reports/ExtraReports.tsx` and
`client/src/utils/exportData.ts`.

Host Availability and Hosts by OS already query Nagios archive availability.
Their existing helper is an integration pattern, not proof that the native
service response has the same shape. Keep those reports' behavior unchanged in
this work.

## Nagios interface to use

Core 4.5.11's official [archivejson source](https://github.com/NagiosEnterprises/nagioscore/blob/nagios-4.5.11/cgi/archivejson.c)
supports `query=availability&availabilityobjecttype=services`, with `starttime`
and `endtime` in UNIX seconds. Unscoped queries return `data.services`. Optional
`hostname` and `servicedescription` selectors can scope it; selecting both returns
`data.service` instead, so the adapter must handle only the documented shapes.

Native rows identify `host_name` and `description`. Duration fields include
`time_ok`, `time_warning`, `time_critical`, `time_unknown`,
`time_indeterminate_nodata`, `time_indeterminate_notrunning` and the four
`scheduled_time_*` fields. These rows do not contain current state, last check,
last state change or plugin output. Do not infer any of those from durations.

Implementation begins with a read-only contract probe of the installed Core:
verify actual JSON types/units, envelope result status, identity fields, empty
and missing history, archive retention/backtracking and initial-state assumptions.
Capture a sanitized fixture from that probe before coding the adapter. Validate
against the same period/options in native Nagios reporting, since defaults and
assumed initial states can change results. Do not assume full `avail.cgi` option
parity merely because both report availability.

Recommended policy: count HARD states, do not invent an initial healthy state,
and show indeterminate time separately. Set supported assumptions explicitly
rather than depending on implicit defaults; confirm the exact parameter names
and behavior with the contract probe. Any intentional difference from existing
host-report assumptions must be documented in the UI and spec, not hidden.

## Calculation and output contract

Normalize native rows once into a shared service-availability representation.
Identity is the exact `(hostname, service description)` pair, never service name
alone. Preserve original names; validate shapes and finite, nonnegative numeric
durations, and reject malformed or contradictory upstream results explicitly.

For one service instance:

```text
known_seconds = ok_seconds + warning_seconds + critical_seconds + unknown_seconds
indeterminate_seconds = no_data_seconds + nagios_not_running_seconds
uptime_pct = 100 * ok_seconds / known_seconds
```

A service's UNKNOWN state is an observed state and belongs in the denominator.
Indeterminate time is missing coverage and is excluded from that denominator;
show its duration alongside known time so 100% uptime cannot hide a large gap.
No known time means null uptime (`—`), not 0% or 100%. Label the value as
availability during recorded time and explain the denominator. Keep scheduled
maintenance included in the headline availability for this initial change;
changing maintenance exclusions is separate scope. Do not subtract scheduled
duration a second time from the native state totals.

Aggregate raw seconds, then calculate and round to two decimal places only at
the response boundary. Do not average percentages or reconstruct seconds from
rounded percentages.

- Network Services: group by exact service description, sum durations across host
  instances, and calculate each group and the overall summary from those sums.
- Device Services: keep one row per host/service pair, group by hostname, and
  calculate each device's service availability from its summed service durations.
  Label this clearly as availability of the device's services, not host uptime.
- Totals count distinct instances/hosts in the archive response. Core enumerates
  configured objects; do not promise archived reports for removed objects.
  No synthetic rows from the Pinpoint history database.

Preserve the existing route URLs, period metadata, grouping arrays and
`uptime_pct` names. Add explicitly named duration fields in seconds to the
instance, group and summary contracts.

### Remove snapshot counts explicitly

Snapshot counts must be removed completely from both Network Services and
Device Services reports, including nested instance rows, API response fields,
TypeScript contracts/adapters, table columns, cards, help text and CSV/XLS/PDF
exports. Remove `total_snapshots` and any equivalent snapshot-count field from
these two report contracts. Do not keep a hidden compatibility count, rename a
count as duration, or put seconds into the legacy `total_snapshots` field.
Inspect and update every caller of these two report endpoints in the same
change. This does not delete stored snapshots or change the general poller.

Replace the Device Services `Snapshots` column/export with `Recorded time` and
add `No recorded data` duration. Use explicit seconds in the API and clear units
in the UI/exports. The existing Host Availability export's legacy count label is
outside this two-service-report scope and must not be changed incidentally.

## Current status versus the report period

Recommended behavior: retain state counts and last-check information as a
separate **Current status** context, fetched in one bulk Nagios `statusjson.cgi`
service-list request per report run. Display an observation time and label the
counts/columns as current, including when the report period is in the past.
This intentionally replaces the old latest-snapshot-within-window semantics.

Join current metadata onto archive instances by the full identity pair. A
missing or pending current result shows unavailable/pending, never automatically
OK or a historical state. A status-request failure can leave a successful
historical report visible with an explicit status-unavailable notice and null
metadata; an archive failure cannot produce an availability report. Avoid adding
new credentials or exposing raw Nagios responses. Reuse existing configured CGI
URLs and server-side authentication; do not invoke the snapshot-writing poller
from a read route.

## Request behavior and UI

- One bulk archive call and at most one bulk status call per report execution;
  group in memory with bounded passes. No per-device/per-service CGI requests.
- Reuse the existing 10-second request timeout and define a bounded total request
  budget; validate periods before any upstream call. Share the archive adapter
  and calculation between the two routes so they cannot drift.
- No new periodic polling job. Keep Run Report and existing period controls.
  A cache is not required initially; measure 90-day performance first. If needed,
  propose bounded caching separately with a visible generation time.
- Archive timeout, auth failure, invalid JSON, failed result envelope or invalid
  row shape: sanitized 502 and a retryable report error. No database fallback.
- Valid empty archive result: empty report. Valid rows with no known time: rows
  with `—` and explicit missing coverage. Preserve loading/error/empty states.
- Keep search, state filters, sorting, ten-row pagination and configured export
  formats. Export the full filtered result and the new duration/coverage columns;
  make units and current-versus-period status clear in headings/help text.
- On a failed rerun, clear or visibly mark prior data stale and disable its
  export until a successful run, so it cannot masquerade as the requested range.
- Keep all existing period values. Resolve the exact same start/end for both
  upstream calls and include that window in report metadata; validate custom
  bounds and server/display time-zone behavior in regression tests.

## Implementation sequence

1. Establish the implementation issue and its acceptance checklist from this
   proposal. Keep the #134 documentation correction separate and retain the
   owner's decision excluding availability targets.
2. Probe the installed Core contract read-only; add sanitized native-shape
   fixtures and failing helper/API tests before changing behavior. Stop if Core
   cannot provide the needed availability data; do not invent a snapshot fallback.
3. Add a service-availability reader and normalizer in
   `server/app/nagios/notifications.py` (extract a focused module only if reuse
   warrants it). Add a read-only bulk service-status reader using existing CGI
   configuration. Test timeouts, envelopes, parsing and credential sanitization.
4. Replace the two snapshot aggregations in `server/app/api/system/report.py`
   with the shared duration calculation; retain permissions and response helpers.
   Update route/module docstrings to describe their actual data sources.
5. Update report wire types, table columns, summary labels, help and exports in
   the existing frontend modules. Add interaction tests for duration rendering,
   missing coverage, current status, failed reruns and export columns.
6. Update the owning backend/data/frontend/status specs together; add a short
   operator explanation of recorded-time availability and archive retention.
7. Run focused tests, `scripts/verify.sh backend`, `frontend`, `docs`, then `all`.
   Run the scoped real-Nagios comparison below and record a sanitized
   `docs/test-runs/` report before declaring complete. No database migration,
   new permission, new dependency or monitoring-configuration change is planned.

## Finish conditions and evidence

- No snapshot-count field (including `total_snapshots`) exists anywhere in the
  Network Services or Device Services report payloads, nested instances, types,
  tables, cards, help or exports. API contract tests assert key absence, and
  frontend/export tests assert the snapshot-count columns/labels are absent and
  recorded-time/coverage durations have correct names and units. No stored
  snapshot data or general polling behavior is removed.
- Both service report uptime values and aggregate values come solely from Nagios
  archive durations. Tests seed conflicting or absent database snapshots and
  prove they have no effect.
- The same service instance has identical durations/uptime in both reports;
  unequal-duration fixtures prove weighted totals and no rounded reconstruction.
- Cover all-OK, mixed states, UNKNOWN, no known time, partially missing history,
  engine downtime and scheduled downtime. A zero-known instance is excluded from
  the weighted denominator but remains visible in coverage/instance counts.
- Cover one state beginning before the range, transitions exactly at the bounds,
  a brief Nagios-recorded outage between Pinpoint polls, custom inclusive dates,
  and malformed/negative/nonfinite values. Fixtures use the real native shape.
- Current metadata is visibly distinct from historical uptime, joined by identity
  with correct pending/missing behavior. No last-check timestamp is fabricated.
- Empty and failed archive responses have distinct outcomes; archive failure
  never falls back to DB values. Status failure preserves historical data only
  with its explicit notice. Login and `system.report` permissions still apply.
- Instrumented tests prove one archive request and at most one status request per
  report execution, independent of host count. Record latency/response size for
  24-hour and 90-day windows and the supported lab inventory; document any
  performance limit rather than asserting untested large-scale capacity.
- Both views' filters, sorting, pagination, custom ranges, rerun/error handling
  and CSV/XLS/PDF paths have interaction coverage. Snapshot counts are absent, with duration/coverage fields in their place. Host/OS reports and alert/notification reports remain green.
- On an exclusively owned lab, compare both views against the installed native
  Nagios availability output using identical windows, state filters and
  assumptions. Verify a brief recorded outage and missing history, and repeat a
  failing case once before filing a separate defect. Record exact tested commit,
  Core version, assumptions, duration/percentage results and verification output.

## Exclusions

Availability targets/SLA pass-fail, recurring emails, host-report redesign,
alert histograms, top alert producers, full outage timelines, downtime exclusion
controls, database cleanup and replacement of the general status poller are not
part of this two-report data-source change. Those can have their own product
requirements after the measured availability foundation is correct.
