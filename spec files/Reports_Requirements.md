# Reports Requirements

Normative behavior of the Reports page (`/reports`, permission `system.report`).
Native references are Nagios Core 4.5.11, the appliance target, not Nagios XI.
Alignment means documented reporting semantics, not copying the legacy CGI pages
or claiming full parity. Route contracts live in
[`Backend_Modules_and_Routes.md`](Backend_Modules_and_Routes.md#reports); component
ownership in [`Frontend_Modules_and_Routes.md`](Frontend_Modules_and_Routes.md#reports).
The operator view is [`docs/manuals/Reports.md`](../docs/manuals/Reports.md) and the
acceptance evidence is the
[#199 lab report](../docs/test-runs/2026-10-18-issue-199-reports/REPORT.md).

## 1. Native behavior and Pinpoint presentation

| Core behavior (source) | Pinpoint presentation |
|---|---|
| Availability reports cover hosts and services over a period ([CGI docs](https://assets.nagios.com/downloads/nagioscore/docs/nagioscore/4/en/cgis.html#avail_cgi)) | Shared period and host/service scope controls |
| `avail.cgi` gives state time, percent of total and of known time, scheduled/unscheduled categories and indeterminate time ([source](https://github.com/NagiosEnterprises/nagioscore/blob/nagios-4.5.11/cgi/avail.c)) | Availability detail drawer: state durations, both denominators, coverage, scheduled/unscheduled split |
| Availability log entries: start, end, duration, state, information | Interval table under the drawer's timeline |
| Trends plots states over a period ([source](https://github.com/NagiosEnterprises/nagioscore/blob/nagios-4.5.11/cgi/trends.c)) | State timeline in the drawer, with an equivalent table |
| Alert Summary: totals by object and top producers ([source](https://github.com/NagiosEnterprises/nagioscore/blob/nagios-4.5.11/cgi/summary.c)) | Alert Summary view; configured group reporting deferred |
| Histogram groups by month, day of month, weekday or hour ([source](https://github.com/NagiosEnterprises/nagioscore/blob/nagios-4.5.11/cgi/histogram.c)) | Alert Histogram with those four recurring breakdowns |
| Alert History filters object and HARD/SOFT; Notifications concern contact deliveries | Alerts and Notifications views with explicit filters |

Pinpoint-specific choices (shown in the UI): the shared applied-query model,
HARD-only problem events as the analysis default, 15-minute hour-of-day slots,
the 90-day bound, and Hosts by OS using Pinpoint OS metadata (not a Core hostgroup
report). No CGI HTML is scraped and the native UI is not embedded.

### Probed archive contract (Core 4.5.11, read-only, 2026-10-18)

`archivejson.cgi` queries `alertlist`, `alertcount`, `notificationlist`,
`notificationcount`, `statechangelist` and `availability`. List queries accept
`start`/`count`. Timestamps are milliseconds, durations seconds, states are
bitmasks (host 1/2/4, service 8/16/32/64) and **state type HARD=1, SOFT=2** (the
`statetypes=hard` filter agrees). `statechangelist` begins with a synthetic
"Initial … Pseudo-State" entry. An unknown host or service answers success with
no object. With a `hostname` the availability answer is a single `host` (or
`service`) object, not `hosts`. A start after the end is `type_code 6`. A
sanitized capture is `server/tests/fixtures/archivejson_core_4_5_11.json`.

## 2. Query model

- Periods: `last_24h` (default), `today`, `last_7d`, `last_30d`, `last_90d` and
  `custom` (inclusive `YYYY-MM-DD`). The server resolves bounds once (server-local
  zone) and returns exact `start`/`end` and the reporting `time_zone`
  (`name`, `utc_offset_seconds`). Rolling and custom requests are limited to 90 days.
- Controls edit a **draft**; **Run Report** applies it atomically. Until then the
  page shows "Changes not applied" and results and exports keep the last applied
  query. An incomplete custom range is never applied. Repeat runs are disabled while
  loading and a superseded response is discarded.
- A failed rerun leaves the previous rows visible but marked stale, with Retry and
  export disabled until a run succeeds.
- Navigation: one row of tabs, the views with summary cards first. Scope: Host (searchable, exact native name) for Host Availability, Hosts by OS,
  Alerts, Notifications, Alert Summary and Histogram; Service (needs a host) for the
  four event views. Controls a view cannot honour are disabled.
- Filters (a button on the control row with a count of applied filters): Objects (host/service/both), State type (HARD/SOFT/both;
  default HARD for analysis, unfiltered for Alerts), Include recoveries, Contact
  (Notifications), Summary grouping and Histogram breakdown. **Clear filters** resets the filter fields (not
  the period) in the draft; Run Report applies it.

## 3. Availability

All four availability views show measured durations and missing coverage. Host
rows distinguish Down and Unreachable; service rows Warning, Critical and UNKNOWN.
Assumptions are explicit and shared by the host report, the service reports and the
drawer: HARD states, `assumeinitialstate=false`, state retention on, state not
assumed during Nagios downtime, 4 backtracked archives. Headline availability uses
known-state time. UNKNOWN is a recorded service state; indeterminate time is
missing knowledge. Null denominators show `—`. Scheduled time is a subdivision of a
state's duration, never extra time. Group time is object-time (e.g. service-hours).
No snapshot count exists anywhere in the host or OS contracts.

Host rows also show the host's **current** state, last check and last state change.
The archive reports durations only, so these come from one bulk current-status read
joined by Nagios host name, the same pattern as the service reports (one status call,
no per-row calls, no snapshots). If that read fails the history is still shown with
an explicit notice and the three fields are empty (`—`); a state is never inferred
from availability. Host Availability lists the hosts of devices that are monitored now;
Missing, paused, retired and merged devices and Nagios's `localhost` are not listed, so
a host that was monitored earlier in the period but is not now does not appear.

### Detail drawer and timeline

Details opens for an exact host or service instance (Network Services rows expand
to instances first). It shows period, reporting zone, source, generation time and
assumptions; a state-duration bar with text legend; the table State / Duration /
% total / % known / Scheduled / Unscheduled; coverage (requested, known, no
recorded data, Nagios no data, Nagios not running, unaccounted); the timeline and an
interval table (start, end, duration, state, information). Segments carry state
text, are keyboard focusable and expose start, end and duration.

Intervals come from `statechangelist` (HARD) and are clipped to the report bounds.
The synthetic initial entry is ignored: time before the first real transition is
`no_data` with an unknown onset, never a healthy state. An earlier recorded state is
clipped to the start and marked "began before this period". The last interval is
"continuing". Clipped duration is labelled "within period only".

Reconciliation: intervals are checked against a second native availability answer
that carries the state through Nagios downtime (event streams continue through
downtime; the displayed totals exclude it, and the drawer says how many seconds).
If they differ by more than 2 seconds, no intervals are returned and the drawer
shows native totals, the per-state differences and the likely cause (for example a
state carried over from before a restart). Intervals are never invented.

## 4. Alerts, Notifications, Summary, Histogram

Alerts: time, host, service, previous and new state, state type, time in previous
state, output. Notifications: time, host, service, state, type, contact, method,
message; every delivery is kept (several contacts are several deliveries). Totals
and cards use the filtered rows. An unavailable source is an error, not zero.
History is linked only for users with `system.history`; the History page's
contracts are unchanged.

Analysis default policy (named above the results): HARD problem events, excluding
recoveries and initial-state entries; controls can include them.

- **Summary:** problem-event totals, host/service split, state counts, distinct
  hosts and objects, recoveries counted separately and never as outages. Grouped by
  host or by exact host/service. Ranking is event count descending, then host name,
  then service name; the first page is the top ten and the full ranking is paged and
  exported. A row opens Alerts with the same period and filters.
- **Histogram:** recurring buckets — Month (12), Day of month (31), Day of week
  (7, Sunday first as in Core), Hour of day (96 slots of 15 minutes). Buckets are
  stable and zero-filled. They recur by wall-clock time in the reporting zone; a
  repeated DST hour counts twice in its bucket and a skipped hour is zero. Chart
  series and table counts agree. A bucket opens Alerts with `recurrence=<breakdown>:<index>`.
  Not a chronological chart (deferred).

## 5. Bounds and completeness

Per report: 15 s per call, a 30 s overall budget, 500-row pages, 45 requests and
20,000 events. Exceeding a limit returns `complete: false` with no totals,
ranking or buckets, and a notice to narrow the period. No per-row upstream calls
and no snapshot or live-status fallback. Details load on demand.

## 6. States, accessibility, exports

Explanatory text (what the report measures, denominators, assumptions, period and
source notes) sits in an "About this report" block below the table, and at the bottom
of the detail drawer, so the controls and results stay uncluttered. The page header
is the title only.

States: loading, permission denied, upstream error with Retry, no matching events,
partial/incomplete, success, stale. Drawers follow DrawerShell, trap focus, close on
Escape and return focus to the opener. Charts have accessible names, text legends and
equivalent tables and use state text, not colour alone, in both themes. Tables scroll
inside the layout and controls wrap. The app shell itself is not designed below
tablet width.

Exports keep the configured CSV/XLS/PDF restriction and export all filtered rows or
buckets, with leading context: period, reporting zone, generation time, source,
filters or policy, units, denominator and warnings (CSV `# key: value` lines, a
header block in XLS and PDF). A stale, failed or incomplete result cannot be
exported. Export logging stays best effort. XLS and PDF values are HTML-escaped.

## 7. Out of scope

Availability targets, SLA indicators, scheduled emails, business reporting periods,
a state-assumption editor, hostgroup/servicegroup management, embedding the Nagios
UI, performance-metric graphs, automatic remediation and any reconstruction from
database snapshots. A chronological per-day alert chart and group reports are
deferred.
