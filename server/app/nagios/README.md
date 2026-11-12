# `app/nagios/` — reading Nagios, and the one writer

Pinpoint reads monitoring data from Nagios Core and never owns reachability.
These modules are imported by the routes and the scheduler; they are not run
directly.

| Module | Does |
|---|---|
| `status.py` | Reads the status JSON CGI and stores host, service and program snapshots in `history.db` |
| `notifications.py` | Reads alert, availability and notification history from `archivejson.cgi` |
| `service_availability.py`, `host_current_status.py` | Read-only bulk history and current status for the reports |
| `mail_failures.py` | Reads a bounded tail of the Nagios log for notification delivery failures |
| `pinpoint_events.py` | Reads discovery scan events |
| `version.py` | Checks the installed Nagios version |
| `commands.py` | The only place Pinpoint writes to the Nagios external command pipe (`NAGIOS_COMMAND_FILE`) |

Who runs it: the scheduler (`app/scheduler.py`, only when `PINPOINT_SCHEDULER=1`)
and the dashboard, report and acknowledgement routes. Connection settings are
`NAGIOS_HOST`, `NAGIOS_PORT`, `NAGIOS_USERNAME` and `NAGIOS_PASSWORD`, listed in
the [root README](../../../README.md#production-settings).

Data semantics (why current state comes from `history.db` but history comes from
the archive CGI) are in [Data Model and Integrations](../../../spec%20files/Data_Model_and_Integrations.md).
