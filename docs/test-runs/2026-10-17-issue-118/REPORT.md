# Test run: issue-118 notification dependencies

| | |
|---|---|
| Date | 2026-10-17 (Asia/Manila; Nagios log timestamps are UTC on 2026-10-16) |
| Commit tested | `986ac2b6` |
| Plan | Issue #118 sections E and G; isolated lab host outage and generated dependency validation |
| Tester | Codex |
| Environment | Docker lab appliance, Nagios Core 4.5.11, five isolated targets on `10.78.0.0/24`; fresh appliance database, existing target containers |
| Raw evidence | `pinpoint-lab-appliance-1:/usr/local/nagios/var/{nagios.log,status.dat}` and `/tmp/issue118-hosts.cfg`, `/tmp/nagios-issue118.cfg` inside that container; generated candidate originated from `/tmp/issue118-render-test/` on the host. Raw files are not committed. |

## Result

**Overall: Pass for the issue's scoped lab checks.** Nagios accepted three generated NCPA service dependencies. During a real outage of a host with three monitored services, it emitted one host notification event and no service notification events while both Pinpoint APIs showed each service's failing state. A real NCPA agent/port failure was not exercised in this Docker lab.

Totals: Pass 6, Fail 0, Blocked 0, Skipped 1.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| Discovery and apply baseline | Pass | `scripts/lab smoke`: 9 passed, 0 failed; six hosts UP. Initial config had no discovered-host services until SSH/HTTP plugins were enabled, so the first `web02` outage was excluded from the suppression result. | — |
| Generate NCPA dependency candidate | Pass | The focused renderer test generated one TCP port service and three metric dependencies in the same candidate, with no literal NCPA token in service commands. | — |
| Nagios validates generated candidate | Pass | A temporary Nagios main config replaced only the `hosts.cfg` reference with the generated candidate. `nagios -v` checked 17 services, 5 hosts, 3 service dependencies; 0 warnings and 0 errors. The running config was not replaced. | — |
| Host-down notification suppression | Pass | Enabled SSH/HTTP plugins, confirmed `web01` had three checked OK services, then stopped the target. Nagios recorded three host alerts (two SOFT, one HARD), one host notification event at timestamp `1792169036` delivered to 28 configured contacts, three service CRITICAL alerts, and zero service notification events for the outage window. | — |
| Service state visibility | Pass | During the outage, Nagios status held three HARD CRITICAL services. `GET /api/system/network-health/services` returned all three as `Critical`/`Hard`; `GET /api/system/dashboard/alerts` returned all three as `CRITICAL` service alerts plus the DOWN host, both HTTP 200. | — |
| Restore targets | Pass | Both stopped targets were started again. Final Nagios status showed `web01` UP and its HTTP, HTTPS and SSH services OK. | — |
| Real NCPA port failure suppresses metric mail | Skipped | Docker targets have no NCPA service installed. Generated objects were validated by Nagios, but no real agent metric/port transition was attempted. | — |

## Deviations from the plan

The initial `web02` outage had no monitored services because the lab starts with plugins disabled. SSH and HTTP were enabled through the supported Plugin Manager API, and the notification trial was repeated on `web01` with three healthy monitored services. The first API poll script incorrectly expected Network Health's title-case `Critical` as uppercase; its response showed the expected state, and a corrected assertion then passed. The `web01` outage and API read were repeated separately to capture both Nagios notifications and both Pinpoint views.

## Follow-up

- Defects found: none.
- Cases to repeat in a lab with NCPA installed: stop the NCPA listener while metrics are failing, confirm the port check is CRITICAL and metric notifications are suppressed, then recover it.
- This run counted Nagios notification events and per-contact dispatches; it did not verify external mailbox delivery.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
