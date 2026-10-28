# Test run: issue-274-presenter-recovery

| | |
|---|---|
| Date | 2026-10-27, Asia/Manila |
| Base and candidate | Base `231b86f7` plus uncommitted candidate. The individual host stop/start used `demo/defense/presenter.py` SHA-256 `684befec130f6556ff4bb026447684b44e7a282b0058c0d03a18a9b4658550a3`; DHCP and Docker restart trials used earlier candidates; the subsequent nine-service stop/restore matrix used candidate SHA-256 `a86269a6a3132a852729f8c1c8998180e8cdb7dc6a7d64daa4fe00d92bdcd4c7`. The SMTP stop/restore was repeated after the host-network guard was added, using candidate SHA-256 `f72695f8ed5c0e14acd81fcaaa29d076de03ff57286f647a86884d522a57a7e4`. |
| Plan | [Defense demo lab](../../plans/Defense_Demo_Lab_Plan.md) |
| Executor | AI-assisted, scripted live pilot |
| Catalog | `manifest.json` SHA-256 `7a2ab626fb66bc71ff660347fd6ba8d118d2c67e600041c84575fa7d47fdc1f8` |
| Environment | Laptop Docker, VirtualBox Windows, isolated `10.77.1.0/27` host-only segment |
| Application / installer | Not tested; appliance integration is pending |
| Baseline / restoration | Fourteen pilot containers and Windows active; DHCP server and the tested client were restored |
| Raw evidence | Console observations; no raw log retained |

## Result

**Overall: Partial.** The tested DHCP and individual host controls worked, and
`presenter up` recovered one statically addressed and one DHCP container after
individual Docker container restarts. A Docker daemon restart, laptop reboot,
reservation changes, DHCP/static transitions, Pinpoint monitoring and full demo
rehearsals remain untested. This is not a product QA or E2E case execution.

| Check | Result | Observed / restoration |
|---|---|---|
| DHCP server fault | Pass | Stopped and started the server; it returned to RUNNING with its saved reservations. |
| DHCP lease | Pass | Released `dynweb02`, then reacquired its reserved `10.77.1.24`; repeated acquire succeeded. |
| Service presets | Pass | Web03 HTTP/HTTPS, api02 HTTP, FTP, SMTP, IMAP, DNS, PostgreSQL, SNMP and SSH stopped and restored with the local listener state checked. An initial SMTP trial revealed a surviving Postfix master; the fixed control was retested successfully. |
| Docker container restart recovery | Pass | Restarted `api02` and `dynweb02`, ran presenter up, and pinged `.5` and `.24` from Windows successfully. |
| Individual host fault | Pass | Stopped `dynweb02` through presenter and started it again; address `.24` returned. |
| Docker daemon restart / host reboot | Not run | The agent session could not authenticate sudo; the owner was asked to run the daemon restart after appliance setup. |
| Appliance and Pinpoint | Not run | The owner is connecting the appliance; registration and monitoring remain pending. |

## Follow-up and sanitization

Issue [#274](https://github.com/esfen14/Pinpoint/issues/274) tracks the remaining
controls, integration and rehearsals. No credentials, private keys, community
values or addresses outside the documented lab range are included.
