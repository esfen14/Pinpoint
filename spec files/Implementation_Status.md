# Implementation Status and Scope

**Snapshot date:** 2026-10-10

This file reports what is present in the repository. It is not a substitute for
the normative behavior in the requirement specifications.

## Implemented backend areas

- Session login/logout and current-user identity.
- Account, role, permission-option, and per-user preference APIs, including the
  bootstrap administrator's first-run setup (`POST /api/user/complete-setup`)
  and server-access recovery (`flask recover-bootstrap-admin`). Recovery privately
  prompts for a policy-compliant temporary password, identifies only the unique
  earliest-created account, preserves setup/status/role/data, forces a password
  change and records a password-free audit event; current sessions continue to
  expire on their configured timeout. The first account (bootstrap administrator)
  is protected from suspension, inactivation, assignment to a role without the
  seven account/role administration permissions, and removal of those permissions
  from its assigned role. Both routes reject before changing persisted data. The
  account and role responses mark the protected choices so their edit forms explain
  the restriction and disable unsafe status, role, and permission controls.
  The built-in `Administrator` role additionally has an immutable permission set
  for every account assigned to it: direct API edits reject changed grants before
  saving metadata, while reordered unchanged grants permit description edits.
  Its name is fixed to preserve the role's built-in identity, and role management
  displays all its permission controls read-only with an explanation.
- Singleton system settings with personal/system separation and optimistic
  version conflict handling. The system Check interval (1/2/5/10/15 minutes)
  generates host and service check intervals through the shared Nagios writer;
  unchanged Nagios `Last_Check` results are not stored again. Plugin status text,
  stale fallback and the per-user browser-refresh hint use the setting. Fresh
  appliance cadence, backup and validation/reload rollback were verified in
  `docs/test-runs/2026-10-10-issue-60/REPORT.md`; controlled full-hour
  before/after rows-per-host measurement is deferred to #82 under the #62 QA
  plan. The short VM comparison is not that measurement.
- Dashboard status, summary, active alerts, acknowledgement, and latest
  notifications.
- Network Health summary, metric trends, plugin grouping, host table/details,
  service table/details, and acknowledgements.
- Alerts and Notifications History list/detail routes backed by Nagios archive
  events and Pinpoint acknowledgement history.
- Header notification feed with per-user unread cursor.
- Nagios command channel (`app/nagios/commands.py`, `NAGIOS_COMMAND_FILE`): acknowledgements and unacknowledgements are sent to Nagios (`nagios_synced` in the response, notice in the UI), and **Check now** (`system.recheck`, 10 s per-target limit) forces a host or service check. Covered by unit and API tests against a temporary FIFO; **not yet verified on a live Nagios appliance** (no lab report in `docs/test-runs/`; run `flask sync-permissions` after deploying to add `system.recheck`).
- Per-user email alert setting (`User.Receive_Email_Alerts`, permission `account.alerts`): only Active opted-in users become Nagios contacts, and account changes that affect a contact rebuild the Nagios config (#80). Verified on the VM lab: contacts follow account changes without a scan, and host and service notifications reach only opted-in users (#80).
- Interface bandwidth: SNMP interface discovery (`snmpwalk`, on demand and after a scan), per-device
  `DeviceInterface` rows, in/out octet Nagios services per monitored interface, the rate calculator
  (`app/bandwidth.py`: 32/64-bit wrap, restart, gap, insufficient data), the bandwidth routes, the
  Network Health Interface Bandwidth card and the drawer's Interfaces section. Unit, API, migration
  and frontend tests pass; **not yet verified against a lab device with a traffic generator** (no
  report in `docs/test-runs/`; the plan is `iperf3` between two lab hosts, comparing the charted
  rate with the generator's). SNMP v3 is out of scope (#14). Interface discovery needs `snmpwalk`
  on the server (net-snmp-utils / snmp), which `check_snmp` already needs.
- Network discovery start/stop/status and Nagios host/service config generation. The reconciliation engine is designed to isolate potential identity conflicts for operator review (creating `DeviceReviewItem` records) rather than silently merging them. This prevents unintended record modification during subnet changes or cloned-identity events (see `device_identity.py`). Duplicates arising from these conflicts persist as `Address Unknown` until manually resolved (Merge/Retire) in the UI through the Devices Inventory "Needs Review" list.
- NCPA eligibility, SSH fingerprint trust (approved key only), login checks,
  deployment with per-device outcomes, cancellation, status, run history and
  review, and trusted-device routes.
- NCPA bootstrap probes log expected missing-account/key exits at INFO while
  preserving creation behavior; unexpected command failures remain ERROR (#47).
- Activity, configuration, discovery, NCPA, and export logs.
- Availability, OS, network-service, device-service, alert, and notification
  report APIs. Host availability and hosts-by-OS reports use Nagios
  `archivejson.cgi` durations, matching Network Health; Nagios failure returns
  502 without snapshot fallback (#92).
- Plugin Manager scanning, inventory, running checks, summaries, details,
  dependencies, enable/disable, validation, custom upload, command overrides,
  updates/rollback, history, and target configuration.
- Scheduled Nagios polling, retention purges, backups, network scans, plugin
  update scans, and security validation.

## Implemented frontend areas

- Login and authenticated application layout.
- Permission-aware sidebar and direct-route guard.
- Dashboard API integration and acknowledgement flow.
- Network Health summary/trend integration.
- Device Inventory backed by latest host-status APIs.
- Account and role management.
- System Settings and per-user preferences. The separate Notification Policy singleton drives generated Nagios timeperiods, contact options and host/service notification settings; Settings → System exposes quiet hours and state/interval controls (`settings.system`). Defaults preserve pre-change `hosts.cfg`. Docker-lab Nagios validation and forced host/service notification dispatch inside/outside quiet hours are documented in `docs/test-runs/2026-10-13-issue-113-notification-policy/REPORT.md`; browser save/reload was exercised via the Docker lab; installer-built VM and inbox delivery are not verified there.
- Settings -> Plugins tab (`settings.plugins`): the SNMP OID table and the NCPA metric table, each editable once its plugin (`check_snmp`, `check_ncpa`) is installed; saving rebuilds the Nagios config. A metric's `fallback_path` (used when no partitions were recorded) is supported by the planner but not editable from the tab.
- Settings -> Email tab (`settings.email`): Gmail over STARTTLS on port 587 with an app password, applied through the installer's root helper; a test email reports a rejected login, blocked port and unknown host separately. Gmail only; Google Workspace and Microsoft 365 (OAuth) and other TLS modes are out of scope. The helper exists only on installed appliances, so saving elsewhere returns "The mail helper is not installed on this server."
- System Logs with five backend categories.
- Reports UI for host availability and network services.
- Plugin Manager inventory/running tabs, details, scan, custom plugin, and
  administrative actions.
- NCPA Deployment page: device list, deploy wizard with host-key verification
  and per-device login checks, live progress, header bell item, and Deployment
  History with run review.
- Header notification feed/unread behavior, session timeout, maintenance banner,
  shared export UI, and network rescan workflow.

## Incomplete or mismatched work

| Area | Current state | Required direction |
|---|---|---|
| History frontend | `/history` is routed to `HistoryPage` with a sidebar entry and the `system.history` client permission, and calls the list and detail routes. It has not been audited against `Alerts_Notifications_History_Requirements.md` | Audit the page against the requirements and fix gaps |
| Nagios command channel lab verification | Code and tests exist; the Nagios `Acknowledgement_Type` change, notification stop and the forced-check result sooner than the scheduled interval have not been observed on a lab appliance | Run the lab steps from the issue and record a sanitized report in `docs/test-runs/` from `TEMPLATE.md`. The downtime command exists in the module but no route uses it (maintenance windows are separate work) |
| Auto-resolved acknowledgements | `AckAction.AUTO_RESOLVED` and model contract exist; status polling does not clean resolved active acknowledgements | On UP/OK transition, delete the active acknowledgement and append an AUTO_RESOLVED history record |
| Per-host alert recipients | Every contact is in one `system_users` group used by all hosts and services | Choose recipients per host (#79), after #80 is verified on the VM lab |
| Discovery stop permission | Stop route checks `network.discovery`; seed data defines `system.discover` | Standardize the route on the seeded permission or deliberately introduce/seed the alternate permission |
| Email alerts and password recovery | Nagios contacts are built from user emails, but nothing configures a mail transport or SMTP relay, so no notification email is sent. The login page's “Forgot Password?” button has no handler and the server has no recovery route (the only reset is an administrator resetting a password). The first-login setup that replaces the installer's placeholder email is #61 (open); mail transport is the installer repository's work; the application-side design is the draft `SMTP_Admin_Email_Plan.md` on branch `docs/smtp-admin-email-plan` (not merged) | Land #61, the installer mail transport and the SMTP settings, then design password recovery on top |
| Reports frontend breadth | Backend has six report endpoints; UI currently exposes availability and network-services views | Add other views only when product requirements call for them |
| Network Health plugin section | Backend endpoint exists; current page does not call `/network-health/plugins` | Connect it when implementing the corresponding `Display_Requirements.md` section |
| Device discovery inventory | Historical docs described `/system/hosts` and port endpoints, but those routes do not exist; current Device Inventory uses latest Nagios host status | Treat the current host-status API as implemented behavior unless a separate discovery inventory contract is approved |
| Plugin lifecycle and discovery | Generation and promotion follow Plugin Manager; the reconciler attaches and detaches services on enable, disable, scan, port edit, merge/retire and NCPA events; the Plugin Manager page shows an enable preview, a Monitoring column, each plugin's monitored services with live status and stop/resume per device. The manual apply routes, `plugin-services.cfg` writing and the `plugin.configure` permission are removed | Not yet run against a live Nagios or checked in a browser: `server/tests/plans/PLUGIN_DRIVEN_MONITORING_LAB_TEST_PLAN.md` is the checklist. Held ports are shown and released from the device drawer's Ports section |
| Plugin-driven monitoring acceptance run | The 2026-10-06 live run found defects D-1 to D-8; code and plan fixes are on `fix/plugin-monitoring-acceptance-defects` but not re-run on the lab. Live status chips, browser UI, NCPA and two journeys were not run | Follow `docs/plans/Plugin_Driven_Monitoring_Remediation.md` |
| Custom plugins | `POST /api/plugin/custom` and its client call are commented out; the Add Custom Plugin button is greyed out | Restore both together when custom plugins enter scope |
| Plugins with no port | Enabling a plugin no longer applies it to every host: services are attached per discovered port, so a plugin that checks no port (`check_ping`, `check_load`, ...) attaches to nothing and cannot be enabled. Accepted: every host keeps the `check-host-alive` host check, and the response time and packet loss on the Dashboard come from it | None; confirm `check-host-alive` in the lab (plan G13) |
| Custom checks | Plugins that probe a device but need arguments (`check_by_ssh`, `check_ups`, ...) take per-device custom checks from the plugin drawer (`plugin.custom_check`); seven more port-driven plugins (`check_pgsql`, `check_ldap`, `check_ldaps`, `check_rpc`, `check_ircd`, `check_time`, `check_ntp_peer`) are in the registry and enable like `check_ssh`. Not run against a live Nagios or opened in a browser | Lab run (`docs/plans/Custom_Checks_Plan.md` phase C4). Server-local plugins (`check_apt`, `check_uptime`, `check_file_age`, ... ) take **server checks** on the Nagios server's own host; the five stock local plugins stay with Nagios Core. Passwords for `check_radius`, `check_mysql_query`, `check_nt` and `check_disk_smb` are stored encrypted (written to `hosts.cfg` in plain text, plan §8b); `check_dbi` and `check_oracle` are not available; see the plan's section 2.4. The ping family (`check_ping`, `check_icmp`, `check_fping`, `check_dig`) takes custom checks like the rest |
| Device Inventory beyond ports | The Ports section of the device drawer exists (state, reason, monitor, ignore, stop, leave suggested, resume, acknowledge, set service, remove pin). The host table shows a monitoring label (Monitored, Missing, Address unknown, Paused, Retired, Merged) with a filter that opens on Monitored, and the drawer pauses and resumes a device (`Include_Device_In_Scanning` now has a writer). A paused, retired or merged device is left out of the dashboard and Network Health counts and alerts. Still API-only: the needs-review list and `SERVICE_CHANGED` items, device confidence badges, address history, merge, retire and static/DHCP marking | Follow-ups in `docs/plans/Device_Ports_UI_Plan.md` §10 and `docs/plans/DHCP_Device_Identity_Plan.md` §11 |
| NCPA port per device | `NCPA_PORT` is one global setting (config only) used by checks, probes and relocation; agents deployed on another port are not tracked | Store the deployed port per device and add a re-port action if the port ever becomes user-configurable |
| NCPA deployment cleanup | A failed install leaves the deployment account, key, sudo rule and helper on the device; the error message says so | Add an explicit cleanup action if operators need it |
| SERVICE_CHANGED auto-clear | A `SERVICE_CHANGED` review item stays open after the mismatch disappears (seen when a port rule was removed); only an operator resolves it | Resolve the item automatically when the port again matches its frozen plugin |
| NCPA token in check command | The NCPA token is a positional argument of the Nagios command, so it is visible in process listings and any transcript of the command | Review passing the token another way (for example a Nagios resource file) |
| CI and automation | CI runs docs links, backend unit tests and frontend test/build on pull requests (`.github/workflows/ci.yml`). Drift checks cover backend routes, browser routes, client API calls, environment variables and QA traceability (`Agent_Workflow_and_CI.md`). CI uploads JUnit test results as artifacts, and sanitized lab reports go in `docs/test-runs/`. The QA journeys, master plan, traceability matrix, resumable `qa-run`/`fix-found` workflows and exact-pinned Playwright role smokes exist. Live Playwright uses a repeatable Staff account and a Docker no-network boundary with a Unix-socket bridge to the lab origin. The administrator and restricted smokes passed on the VM lab on 2026-10-11. Full J2/J3 acceptance remains partial. Not automated: deployment, installer ISO build and headless install test, a permissions drift check, branch protection | Complete the remaining live QA cases; require the CI jobs on `main`; add an installer build/install job when that repository's scope is agreed |
| Frontend lint | `npm run lint` has 0 errors and blocks CI. 24 `react-hooks/set-state-in-effect` warnings remain (the rule is set to `warn` in `client/eslint.config.js`): pages and components that set state inside effects | Refactor each (derive state, key the component, or fetch with an event/subscription), then set the rule back to `error` |
| Local lab | `scripts/lab` and `lab/` give a Dockerized appliance and five targets for QA; build, discovery, Nagios reload and `scripts/lab smoke` verified. Plugin enablement, `break`/`fix` and Nagios host/service notification dispatch were exercised for issue #113 in `docs/test-runs/2026-10-13-issue-113-notification-policy/REPORT.md`; `ui`, `sync`, actual mail delivery and NCPA install (targets have no init system) remain unverified. Not in CI | Finish the unverified commands, add plugin and alert checks to `lab/smoke.py`, then consider a CI job |
| VM lab | `scripts/vmlab` builds a VirtualBox appliance from the stock Ubuntu ISO, snapshots Ubuntu + Nagios below the app, installs a pushed branch with the installer's own steps, and runs the installer healthcheck and a smoke test against the `demo/` targets. First run passed (healthcheck 59/0; five targets monitored; see `docs/test-runs/2026-10-08-vm-lab-first-run/`) and found #43. NCPA run (`docs/test-runs/2026-10-08-ncpa-run/`): deployment to two targets passes, but NCPA services are CRITICAL on installer-built appliances because `check_ncpa.py` needs a `python` command (#45). The installer fix (`e471a1b8`, branch `fix/check-ncpa-python3-shebang`, not merged) was inspected and one NCPA check returned OK on a partial rerun (`docs/test-runs/2026-10-08-ncpa-repeat-run/`, Partial); a later clean run (`docs/test-runs/2026-10-08-ncpa-fresh-run/`) passed the fresh install, all six NCPA services OK and the negative tests, and the installer fix is merged (`2859361d`). The run found a duplicate `Address Unknown` device record for one host (#59); the discovery start race and address-unknown matching are fixed and the fresh VM-lab repeat recorded one ACTIVE record after NCPA deployment (`docs/test-runs/2026-10-10-issue-59/`), though #86 tracks remaining duplicate persistence seen on the inherited lab baseline. Not run: alerts, `demo_lab.py break`/`fix`, `sync --client` | Fix #45 (mainly the installer), rerun the NCPA monitoring cases, then run alerts and `break`/`fix` |
| Installer | Developed in another repository | Keep installer work out of this repository unless scope changes |

## Test approach status

Backend tests are organized under `server/tests/unit/`, `integration/`, `e2e/`,
`support/`, and `plans/`. Default pytest collection is isolated. The deterministic
browser-to-Nagios approach is recorded in
[`TEST_APPROACH_ADJUSTMENT_PLAN.md`](../server/tests/plans/TEST_APPROACH_ADJUSTMENT_PLAN.md)
as **Proposed — implementation deferred pending fixes**. Missing UI workflows,
complete orchestration and automatic disposable-instance recovery are not yet
implemented; existing harness improvements do not satisfy full acceptance.

## Explicit exclusions

- Backend network-topology computation is not part of the current release.
- The frontend topology view is not a supported current-release page. Source may
  remain dormant for future development.
- Nagios' native UI is not a Pinpoint operator surface.
- Plugin Manager does not install arbitrary agents or plugins on monitored
  devices; it manages plugins on the Pinpoint/Nagios server.

## Status maintenance

When completing an item above, update this file in the same change. When a new
route, page, model, or workflow lands, also update its owning architecture or
catalog specification. Do not preserve stale “not built” notes after the code is
implemented.
