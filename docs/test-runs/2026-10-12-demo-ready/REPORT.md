# Demo setup: demo-ready

| | |
|---|---|
| Date | 2026-10-12 |
| Commit tested | Appliance application `6b558198`; installer checkout `2859361` |
| Plan | [Demo walkthrough](../../../demo/DEMO_READY.md) |
| Tester | Codex, at the lab owner's request |
| Environment | Ubuntu 22.04.5 appliance, Nagios Core 4.5.11, five Ubuntu 24.04 targets, isolated `10.77.0.0/28`, fresh application databases |
| Raw evidence | Local tool transcripts and VirtualBox console captures; not committed |

## Result

**Overall: Partial for the full-system demonstration.** Installation, target
services, discovery and web01 agent deployment were observed successfully.
The installed appliance snapshot is saved. Browser journeys, alert
acknowledgement/recovery and SMTP delivery were not rehearsed in this setup.

## Checks

| Check | Result | Observed behavior | Issue |
|---|---|---|---|
| Appliance installation | Pass | Installer deploy and privilege steps completed on application main `6b558198`. Initial healthcheck: 60 passed, zero warnings/failures. Final healthcheck: 59 passed, one warning, zero failures; the warning counts earlier failed SSH probe tracebacks. | — |
| Target services | Pass | All five restored target VMs booted and management SSH answered. The wall showed every expected SSH, HTTP/HTTPS and SNMP service Up, including HTTP 8080 and SSH 2222. | — |
| Restricted discovery | Pass | Read-back confirmed only `10.77.0.0/28`. The final smoke run completed discovery and applied Nagios config in 92 seconds; all five expected addresses were monitored and Up. Nine smoke checks passed. | — |
| Presentation configuration | Pass | Plugin inventory scan succeeded; HTTP, SSH, SNMP and NCPA plugins enabled through the API. Check interval set to one minute, session timeout to 120 minutes, maintenance disabled. | — |
| Monitoring baseline | Pass | Before agent deployment, Network Health showed six hosts Up, all 23 services OK and zero active alerts. | — |
| NCPA deployment | Pass | Web01 retry completed in 30 seconds: host-key read/trust, SSH login/sudo, deployment and Deployed NCPA state all passed (10 checks). Legacy01 remains pending for the live wizard. | — |
| NCPA metrics and appliance reboot | Pass | After the saved appliance booted, CPU, memory and root-disk services reported OK. The service API listed 26 services, all OK. | — |
| Installed snapshot | Pass | Powered-off `demo-ready` snapshot created on `pinpoint-qa-appliance`; UUID `816aba9f-d9fa-40c5-bb42-bc6d6c8417d9`. The lower `os-nagios-ready` snapshot is retained. | — |
| Alert/browser walkthrough | Skipped | Presenter steps are documented; no browser or alert lifecycle acceptance pass is claimed. | — |
| Email delivery | Skipped | Gmail SMTP credentials were not supplied or configured. | — |

## Setup recovery

- Existing target instances were running in an older VirtualBox session even
  though the current session listed none. Starting visible instances duplicated
  the lab IPs and led to target filesystem errors. Both sets were stopped; the
  targets were restored from their clean `demo-ready` snapshots and started once.
  The final discovery run above occurred after recovery. No product defect is
  inferred from this environment conflict.
- Web01's first agent install after recovery encountered Ubuntu's automatic
  update holding the dpkg lock. The update completed; the next API deployment
  succeeded without changing application code. Its failed deployment record
  remains visible in Deployment History.

## Limits and follow-up

The walkthrough is a presenter guide, not a full QA sign-off. Rehearse alert
acknowledgement/recovery and the legacy01 NCPA wizard before presenting. An
appliance snapshot does not restore targets; keep their agent state consistent
with the appliance when restoring it.

## Sanitization

No passwords, tokens, keys, communities, databases, VM disks, raw configuration
or private addresses outside the documented lab subnet are included.
