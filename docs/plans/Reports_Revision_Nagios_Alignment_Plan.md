# Reports revision aligned with Nagios Core

Status: proposed implementation backlog — requested 2026-10-17; no application
changes made. Implementation issue: [#199](https://github.com/esfen14/Pinpoint/issues/199).
Priority: Low. Labels: `Low Priority`, `enhancement`, `web-interface`.

Related work: [#134](https://github.com/esfen14/Pinpoint/issues/134) corrects
existing report documentation; [#198](https://github.com/esfen14/Pinpoint/issues/198)
moves the two service reports to Nagios durations and removes their snapshot
counts. This revision depends on #198 for service availability, reuses its
contracts, and adds reporting depth and a coherent UI. It must not duplicate
that implementation or reintroduce snapshot calculations.

Feeds [Frontend modules and routes](../../spec%20files/Frontend_Modules_and_Routes.md),
[Backend modules and routes](../../spec%20files/Backend_Modules_and_Routes.md),
[Data model and integrations](../../spec%20files/Data_Model_and_Integrations.md)
and [Implementation status](../../spec%20files/Implementation_Status.md).
Create a focused Reports requirements specification and route it from AGENTS.md
when implementation starts; Display Requirements currently owns Dashboard and
Network Health, not a complete Reports product contract.

## 1. Problem and objective

The existing six views provide tables and basic cards, but limited explanation
of historical availability, missing coverage, maintenance, outage intervals and
repeated alerts. Present the reporting questions supported by Nagios Core in
Pinpoint's existing interface, with explicit data sources and readable labels.
Alignment means documented reporting semantics, not copying the legacy CGI
appearance or claiming full feature parity. The reference is Core 4.5.11,
Pinpoint's appliance target, rather than Nagios XI.

## 2. Cited Nagios behavior and proposed mapping

The official sources below were consulted on 2026-10-17. Each row separates the
observed Core behavior from the proposed Pinpoint presentation.

| Nagios Core behavior and citation | Proposed Pinpoint UI |
|---|---|
| Availability reports cover hosts and services over a selected period. [Official CGI documentation](https://assets.nagios.com/downloads/nagioscore/docs/nagioscore/4/en/cgis.html#avail_cgi) | Shared report period and host/service scope controls |
| `avail.cgi` presents state time, percent total time, percent known time, scheduled/unscheduled categories and indeterminate time. [Core 4.5.11 availability source](https://github.com/NagiosEnterprises/nagioscore/blob/nagios-4.5.11/cgi/avail.c) | Availability detail drawer with state-duration table, both denominators, missing coverage and maintenance breakdown |
| Availability log entries include start, end, duration, state and information. [Core 4.5.11 availability source](https://github.com/NagiosEnterprises/nagioscore/blob/nagios-4.5.11/cgi/avail.c) | Bounded interval table beneath a selected object's timeline |
| Trends plots host/service states across a requested period. [Official CGI documentation](https://assets.nagios.com/downloads/nagioscore/docs/nagioscore/4/en/cgis.html#trends_cgi), [Core 4.5.11 Trends source](https://github.com/NagiosEnterprises/nagioscore/blob/nagios-4.5.11/cgi/trends.c) | State timeline in the availability drawer, paired with an accessible interval table |
| Alert Summary offers totals by object/group and top alert producers. [Core 4.5.11 summary source](https://github.com/NagiosEnterprises/nagioscore/blob/nagios-4.5.11/cgi/summary.c) | Alert Summary view with host/service totals and a ranked producer table; configured group reporting deferred |
| Histograms group alerts by month, day of month, weekday or hour of day. [Core 4.5.11 histogram source](https://github.com/NagiosEnterprises/nagioscore/blob/nagios-4.5.11/cgi/histogram.c) | Alert Histogram view with these four recurrence breakdowns and a matching data table |
| Alert History filters host/service problem events and HARD/SOFT states; Notifications concerns contact deliveries. [Official CGI documentation](https://assets.nagios.com/downloads/nagioscore/docs/nagioscore/4/en/cgis.html) | Separate Alerts and Notifications views with explicit object/state-type or contact filters |

These references establish the native behavior, not the feasibility of every
JSON field. Read-only probes of the installed archive JSON API must establish
what is available before building adapters. Do not scrape CGI HTML or expose
Nagios's native UI as Pinpoint's operator interface. Assumption differences
between native HTML and JSON output must be visible in comparison evidence.

## 3. UI structure

Retain `/reports` and `system.report`. Use a report selector grouped by purpose
rather than adding another crowded row of tabs:

| Group | Reports |
|---|---|
| Availability | Host Availability; Network Services; Hosts by OS; Device Services |
| Events | Alerts; Notifications |
| Analysis | Alert Summary; Alert Histogram |

The six existing views remain reachable under their existing names. Preserve
search, sorting and ten-row table paging. Analysis is new functionality. A state
timeline is a drilldown for one host or service, not an additional global tab.

Proposed page wireframe (layout proposal, not an implemented screen):

```text
Reports                                      [Report: Host Availability v]
What this report measures
[Period v] [Host: All v] [Service: All v]             [Run Report]
[Custom start/end when selected] [Advanced filters v]

Selected range + reporting time zone | Generated at | Source: Nagios archive
[Objects] [Availability: known time] [Problem time] [No recorded data]
[Scope/coverage/partial-data notice when needed]

[Search] [Sort]                              [Export v]
Hostname | Availability | Down time | Unreachable time | No data | Details
...10 rows...                                               [Pagination]

Details drawer: selected object and exact period
[State-duration bar + text legend]
State | Duration | % total time | % known time
[Scheduled / unscheduled breakdown]
[State timeline]
Start | End | Duration | State | Information
[Open matching History, when permitted]
```

Current status supplied by #198 is a clearly separated optional context section,
with its own observation time; it is not a headline historical-period card.
When no current-status permission/data is available, the historical report
continues to work according to its report permission and source availability.

### Shared query controls

Keep `last_24h`, `today`, `last_7d`, `last_30d`, `last_90d` and custom inclusive
dates. The server resolves bounds once and returns exact timestamps and the
reporting time zone. Do not silently reinterpret Today/custom boundaries in a
different browser zone. Display timestamps can follow user preferences while
the report explicitly names its boundary/bucketing zone.

Host and service selectors are searchable and represent exact native identities;
service is disabled when inapplicable. Event views offer Host / Service / Both,
state filters and HARD / SOFT / Both. Default alert analysis is HARD problem
events, excludes recoveries and initial-state entries, and names that policy
above its results. Explicit controls can include them. Notifications additionally
filter contact and notification type where native data supports them.

Controls edit a draft query; Run Report applies it atomically. Change of report
runs its applicable default/current query. Editing filters shows "Changes not
applied" and export stays tied to the last successful applied query. Disable
repeat runs while loading, cancel or discard superseded responses, and retain
focus. This is a deliberate proposal replacing inconsistent implicit reruns.

### Availability views and details

All four availability views show measured durations and missing coverage.
Host rows distinguish Down and Unreachable; service rows distinguish Warning,
Critical and UNKNOWN. Hosts by OS retains Pinpoint OS metadata and cannot claim
to be a native Nagios hostgroup report. Service summaries use #198's weighted
seconds, never average percentages. Group-level time is labelled object-time
(e.g. service-hours), since summed durations can exceed the wall-clock range.

Headline availability uses known-state time as agreed in #198. Details also
show percent of total requested time and recorded-time coverage. UNKNOWN is a
recorded service state; indeterminate time is missing knowledge. Null denominators
show `—`. Scheduled time is a subdivision of state totals, not extra time to add;
show it separately without silently excluding it from the headline percentage.
Include no-data reasons where native output supports them.

Remove the legacy Host Availability `Total Snapshots` export field and any
remaining snapshot-count references in host/OS report contracts, types and UI;
use explicit duration fields instead. #198 owns the same removal for services.
Preserve stored history data and the regular poller. No compatibility field may
mislabel seconds as snapshots.

Click Details on a host or exact service instance to load one interval timeline.
Network Services group rows expand to instances first. Timeline segments use
state text as well as color; keyboard focus and hover expose start/end/duration.
The adjacent table exposes every segment without requiring pointer interaction.
Clip intervals to the report bounds. Mark continuing intervals and unknown
onsets/endings honestly; an absent predecessor is not a recovery or healthy
state. Label clipped duration distinctly from full outage duration. Current
object enumeration/retention can limit removed-object reporting; state that
limit rather than generating historical rows from database snapshots.

### Alerts and Notifications

Alerts show time, host, service, prior/new state, state type, output and available
duration context. Notifications show time, host, service, state/type, contact,
method and message only when supplied. Preserve every delivery record; multiple
contacts are multiple deliveries, not duplicate alerts. Their totals and empty
states use the same applied filters as the table. Distinguish an unavailable
source from zero events. Use existing History routes for detailed investigation
only if the user also has `system.history`; do not grant access through links.

### Alert Summary and Histogram

Summary shows problem-event totals by host or exact host/service identity,
state counts, distinct affected objects and a top-producer ranking. Default
ranking is event count descending with deterministic identity ties, showing the
top ten and allowing the full ranked table to be paged/exported. A row opens
Alerts using the same period and filters. Recovery counts, when enabled, are
separate from problem counts and never treated as outage counts.

Histogram uses recurrence categories Month, Day of month, Day of week and Hour
of day (15-minute slots), following the cited Core breakdowns. Label them as
recurring buckets, not a chronological history chart. Keep stable bucket ordering
and zero buckets, name the bucketing time zone, and define DST repeated/skipped
hour handling. Chart state series and tabular counts must agree; selection opens
matching alerts using an explicit recurrence filter. Export the bucket table,
not a screenshot. A chronological per-day chart is deferred.

### Feedback, accessibility and exports

Provide loading, permission denied, upstream error with Retry, no matching
objects/events, insufficient history, partial coverage and successful generation
states. No snapshot fallback. Failed reruns leave previous results visibly stale
and disable export until success. Large tables scroll within the layout; controls
wrap on narrow screens, with no clipped actions. Drawer follows DrawerShell
conventions, focus trap/return and Escape behavior. Charts have accessible names,
text legends and equivalent tables; colors work in both themes.

Keep configured CSV/XLS/PDF formats. Export all filtered rows/buckets, including
period, scope, reporting zone, generation time, source, denominator/assumption
labels, coverage and applicable warnings. Explicit units accompany durations.
The print view includes textual chart equivalents. A partial upstream fetch
cannot be exported as a complete result. Export logging remains best effort.

## 4. Backend and data work

Extend `server/app/api/system/report.py` and reusable Nagios archive readers;
keep server-side login and `system.report` checks. Use #198's service duration
adapter and existing host availability reader. Add typed event/interval adapters
and server aggregation for summary/histogram. Do not pull a page of events into
the browser and call it the network total. Do not change the History page's
contracts as a side effect.

Proposed read-only endpoints under `/api/system/report`: `/availability-detail`
(exact host, optional service, period), `/alert-summary` and `/alert-histogram`.
These are proposals requiring route docstrings, validated query contracts, exact
identity encoding and route/client drift entries in the implementation PR.
Reuse existing alerts/notifications endpoints for their view filters when safe.

The detail reader needs state changes at/before the lower bound and transitions
through the upper bound, plus engine/downtime context. Use native availability
for totals and archive events for intervals; normalize assumptions explicitly.
Probe the installed API before fixing a schema. If an interval source cannot
reconcile with the native duration totals, report the discrepancy and stop that
feature rather than inventing intervals. No live status or snapshot inference
may fill missing historical state.

Bound archive calls with timeouts, an overall budget, validated ranges and
pagination/continuation that detects truncation. Default UI periods remain at
most 90 days; custom requests are limited to 90 days initially, with clear
validation. Preserve predecessor context without scanning unlimited archives.
Use bounded traversal for aggregates: if completeness cannot be proven, return
an explicit incomplete/error state and suppress definitive totals. Set and test
concrete request/row/time limits after the contract probe, before coding the
production reader. No per-row network calls; details load on demand. No new
background jobs, migrations, dependencies, credentials or new permissions are
expected. Do not edit Nagios logs, retention settings or config for this feature.

## 5. Implementation sequence and scope boundaries

1. Complete #198 and rebase the reporting revision; inspect actual installed
   Core JSON interfaces and document limits/assumptions in sanitized fixtures.
2. Write the focused Reports requirement specification, finalize query/response
   contracts and add failing backend semantic tests. Establish completeness and
   performance limits. This low-priority issue may be split into linked child
   issues by phase before implementation, retaining the complete checklist.
3. Implement shared report controls, applied-query state, duration/coverage
   columns, host snapshot-label removal and the accessible detail drawer.
4. Add interval/timeline reads and maintenance breakdown with native comparison.
5. Add Alert Summary and Histogram adapters/UI; wire event/contact filters and
   scope-preserving drilldowns. Reuse current modules; split ExtraReports into
   focused components as needed rather than adding a second reporting system.
6. Update exports/help/specs and run focused tests then backend/frontend/docs/all.
7. Compare real data with the installed native Core report pages and archive
   output on an exclusively owned lab; commit sanitized evidence before claiming
   parity. No screenshot or fixture-only test establishes native parity.

No availability targets, SLA indicators, scheduled emails, business reporting
periods, configurable state-assumption editor, hostgroup/servicegroup management,
full Nagios UI embedding, performance-metric graphs, automatic remediation or
historical reconstruction from database snapshots. Existing System Logs and
History remain their respective operator tools. Group reports and additional
calendar presets can be proposed later; do not claim full Core reporting parity.

## 6. Finish conditions and verification

- [ ] Cited native behavior is mapped to each delivered feature; the UI clearly
  identifies Pinpoint-specific choices and any tested native/JSON differences.
- [ ] #198's source/weighting/removal contract remains intact; host/OS legacy
  snapshot-count fields/labels are removed without deleting stored snapshots.
- [ ] All six existing views remain, with shared period/scope/applied-query
  controls, correct custom/time-zone bounds, permissions and distinct historical
  versus current context. Draft edits, races and failed reruns cannot export
  mismatched or stale data.
- [ ] Availability details show state durations, total/known percentages,
  coverage, no-data reasons when available, and scheduled/unscheduled subdivisions
  without double counting. Weighted group totals use explicit object-time units.
- [ ] Exact-object detail includes accessible timeline and interval table, with
  clipped, continuing and unknown-boundary behavior tested and reconciled with
  native totals under matching assumptions.
- [ ] Alerts and Notifications have their specified filters/columns, consistent
  totals, correct contact-delivery semantics and permission-safe History links.
- [ ] Summary has host/service totals, distinct-object counts, deterministic
  top-producer rankings and scope-preserving alert drilldowns. Counts use the
  complete filtered archive result, not a table page or fabricated outage count.
- [ ] Histogram implements all four cited breakdowns, stable/zero buckets,
  explicit reporting zone/DST semantics, equivalent table/export values and
  recurrence-filter drilldown; no chronological-chart parity claim.
- [ ] Loading/error/empty/insufficient/partial/success states, narrow layouts,
  keyboard/focus behavior, non-color state cues and both themes are verified.
- [ ] CSV/XLS/PDF retain configured restrictions, export full applied results
  with required metadata/units/warnings, omit snapshot counts, and prevent a
  truncated or failed fetch being presented as a complete report.
- [ ] Native-shape API tests cover mixed states, UNKNOWN versus no history,
  maintenance, pre-range onset, exact bounds, continuing outages, irregular
  intervals, partial/truncated archives, removed objects, auth/timeout/malformed
  responses and zero denominators. Event tests cover HARD/SOFT, initial entries,
  recoveries, multi-contact deliveries, ties, recurrence and DST boundaries.
- [ ] Instrumented tests verify bounded requests/work, concrete completeness
  limits, no per-row queries and no snapshot fallback. Record 24h/90d timings
  and supported-lab inventory; document larger-scale limits honestly.
- [ ] Implementation updates Reports requirements plus frontend/backend/data/
  status specs, routing/index links, help and operator documentation in the PR.
  Route contracts and permissions remain aligned; no unrelated behavior changes.
- [ ] Focused backend/frontend tests and `scripts/verify.sh all` pass with actual
  output attached to the PR; existing report and History regressions remain green.
- [ ] A sanitized `docs/test-runs/` report records exact app/Core versions,
  assumptions, matching bounds, native-versus-Pinpoint durations/events/buckets,
  brief outage/missing-history/maintenance cases, UI/export journeys and limits.
  This issue authorizes those scoped checks on an exclusively owned lab, not an
  unrelated QA sweep, destructive reset or production-device mutation.
- [ ] A PR links the implementation issue, describes changes/evidence and has
  green required CI; human review and blocking-comment resolution remain merge
  gates. No functionality is claimed complete just because a plan was filed.
