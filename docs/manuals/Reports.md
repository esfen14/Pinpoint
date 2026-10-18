# Reports

Open **Report** in the sidebar. Needs the `system.report` permission.

## Choosing a report

The tabs list the views with summary cards first (Host Availability, Network
Services, Alerts, Alert Summary, Notifications), then Hosts by OS, Device Services and
Alert Histogram.

## Running one

1. Pick a report tab and a **Period** (up to 90 days; custom dates are inclusive).
2. Click **Filters** to scope the report: **Host** (and **Service** for event reports;
   the lists fill from reports you have already run, or type an exact name), object
   type, HARD/SOFT, recoveries, notification contact, summary grouping and histogram
   breakdown. Only filters the current report uses are shown.
3. The button shows how many filters are applied. **Clear filters** in the panel resets the
   filter fields (not the period); click **Run Report** to apply.
4. Click **Run Report**. Until you do, the page says "Changes not applied" and the
   table and export still show the previous run. If a run fails, the old rows are
   marked stale and cannot be exported; use **Retry**.

All times in a report are measured over the period shown, in the server's reporting
time zone (named in the report and in exports).

## Reading availability

- **Availability %** is time in the good state divided by *known* time. Time Nagios
  has no record of is shown separately as "No recorded data" and is not counted.
- Durations are in seconds (or a readable form in the drawer).
- Click **Details** on a host or service (for Network Services, show the instances
  first) to see state durations, both percentages, coverage, the scheduled
  (maintenance) part of each state and a timeline with an interval table.
- If the timeline cannot be matched to Nagios's own totals, the drawer says so and
  shows the totals only. It never guesses intervals. Typical cause: a state carried
  over a Nagios restart.

## Alert Summary and Histogram

Counts are *alert events*, not outages. The default is HARD problem events; recoveries
are counted separately when you include them. **Open alerts** on a row or histogram
bucket shows the matching alerts for the same period. The histogram groups events by
recurring time of month, day, weekday or 15-minute slot, not as a timeline.

## Exporting

**Export** offers the formats enabled in Settings. Files start with the period,
reporting zone, generation time, source, filters, units and any warnings. Incomplete
results (too many events) cannot be exported; narrow the period.
