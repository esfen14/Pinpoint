# `server/scripts/` — Nagios-side helper scripts

Standalone scripts that **Nagios runs on the appliance** as the `nagios` user. They use only the standard library, do not import the Flask app, and start with `#!/usr/bin/python3 -I`. The installer copies them into place; nothing here is run by hand in normal use.

| Script | Run by | Does |
|---|---|---|
| `pinpoint_event_handler.py` | Nagios, on a covered host or service state change | Validates its arguments and writes one note to the spool folder (`REMEDIATION_SPOOL_DIR`); the app's consumer (`app/remediation.py`) decides what to do. See [Event Handler Security Review](../../docs/archive/plans/Event_Handler_Security_Review.md) |
| `pinpoint_notify_email.py` | Nagios notification commands | Builds and sends one notification as an HTML email with a plain-text part |
| `pinpoint_check_ncpa.py` | Nagios service checks | Runs the installed NCPA client with a protected token read from the resource file |
| `pinpoint_check_native.py` | Nagios service checks | Supplies passwords to supported native plugins through stdin instead of argv |
| `build_plugin_descriptions.py` | A developer, at development time | Regenerates `app/api/plugin/plugin_catalog_data.py`; the result is committed and the server never fetches it at runtime |

Changing an installed script changes every appliance on upgrade, so raise it
with the installer owners first ([installer contract](../../spec%20files/Agent_Workflow_and_CI.md#deployment-environment-installer-contract)).
