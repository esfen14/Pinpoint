# Reading service availability reports

Network Services and Device Services use Nagios archive durations. Run Report
loads the selected historical range and separately reads current Nagios status.
There is no extra polling schedule or availability target.

Availability during recorded time is OK seconds divided by OK + Warning +
Critical + Unknown seconds. Maintenance remains included: the matching scheduled
state seconds are added once to the ordinary state seconds. UNKNOWN is a recorded
state, not missing history. No known state time displays `—`, never 0% or 100%.

Always read the coverage columns alongside the percentage. “Recorded time” is
the known-state denominator. “No recorded data” is time excluded from that
denominator, broken down into Nagios-reported no data, engine not running, and
unaccounted time. Unaccounted means the returned duration fields do not explain
that part of the requested window; it does not identify a cause or an outage.
For example, one recorded healthy hour and 23 missing hours displays 100% during
recorded time, one hour recorded and 23 hours without recorded data.

Network Services groups exact service descriptions across hosts. Device Services
keeps each host/service pair and aggregates its services; this is not host uptime.
Aggregates weight elapsed seconds, not service percentages. Summed instance time
can exceed the calendar range: two services over a day can contribute 48 hours.
A service with zero known time remains in instance counts and coverage totals.

Current states, last check and last state change describe the time the report
ran, even when you request a past period. The observation timestamp identifies
that separate context. Pending means no completed check; unavailable means no
matching current result or a failed status request. A status failure leaves the
historical report visible with a notice; an archive failure requires retry and
clears the old result so it cannot be exported as the newly requested range.

All existing periods remain available. Custom dates are inclusive in the server's
local calendar; the shown end is exclusive at the next midnight. Reports stop at
the last completed second, including a custom end that reaches the future. The
exact bounds show using your display-time preference. Excluding the current
second prevents Core 4.5.11 from substituting current state for missing history.
Service requests explicitly use HARD states, no assumed initial state, no assumed
state during engine downtime, state retention and four backtracked archives.
Existing host reports keep their separate assumptions and legacy count label.

Nagios can report only what it checked, recorded and retained. Four preceding
archives are searched for an initial state; deleted logs and unobserved outages
cannot be reconstructed. Nagios enumerates currently configured objects, so
removed services may be absent from historical reports. Pinpoint does not fill
these gaps from its database snapshots. Operators should retain Nagios archives
for their reporting needs; this feature does not change rotation or retention.

Search, existing state filters, name sorting and ten-row pages remain. CSV, XLS
and PDF export every filtered row, including duration fields labelled in seconds
and explicitly current status columns. The PDF option opens the browser's print
view. Export formats continue to follow the system's configured allowed formats.
