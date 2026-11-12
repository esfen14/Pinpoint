# Archived plans

Design and implementation plans for work that has shipped. Read them for the reasoning behind a
design; do not treat them as current requirements.

| File | What it was for |
|---|---|
| `Custom_Checks_Plan.md` | Per-device custom checks for plugins that need arguments |
| `Device_Monitoring_State_Plan.md` | Pause/resume and the monitoring-state label in Device Inventory |
| `Device_Ports_UI_Plan.md` | The Ports section of the device drawer |
| `DHCP_Device_Identity_Plan.md` | Stable device identity across DHCP changes (proposal). Phases 0 to 4 (back end) were built; NRDP (phase 5) was not. |
| `DHCP_Device_Identity_Implementation_Report.md` | What was built from that plan and what was not |
| `Event_Handler_Design.md` | Allowlisted Nagios event handler framework (#120) |
| `Event_Handler_Security_Review.md` | Security checklist for the event handler design |
| `Proactive_Resolution_Implementation_Plan.md` | Umbrella plan for automatic recovery (#120 to #121, #153 to #156) |
| `Issue_8_3_Remote_Restart_Design_Note.md` | Remote service restart on monitored devices (#121) |
| `Issue_182_Remote_Restart_Security_Review.md` | Security review of remote restart |
| `Issue_129_Check_Secret_Transport.md` | How NCPA and SMB secrets reach check commands (#129) |
| `Issue_191_Account_Creation_Investigation.md` | Why account creation failed (#191) |
| `Installer_Handoff.md` | Installer work list. Done in the installer repo as of 2026-11-11, except the narrower `nagios` group rights (D1, needs a person to confirm the list), implicit TLS for SMTP (deferred) and two optional wrappers (`recover-bootstrap-admin`, `restore-backup`) |
| `Installer_Instructions_Proactive_Resolution.md` | Installer instructions for the event handler and restart rule (built) |
| `Defense_Demo_Lab_Plan.md` | The isolated fifteen-device defense demo lab (#274). Delivered as a laptop Docker lab (`demo/`). Gaps recorded in `Implementation_Status.md`: no licensed Windows VM, two full rehearsals not completed, and some planned commands replaced by `presenter.py`. |
| `DHCP_Lab_Extension_Proposal.md` | The isolated Docker DHCP lab (#187), now in `lab/dhcp/` and the Local Lab manual |
| `VM_Lab_Plan.md` | The real-appliance VM lab (`scripts/vmlab`): create, provision, install, snapshot and run acceptance on a real appliance. The procedure is still what `scripts/vmlab` implements. |
| `Live_Test_Remediation_Plan.md` | Fixes from the first live NCPA test |
| `NCPA_Deployment_UI_Plan.md` | The NCPA deployment wizard and run history |
| `Plugin_Driven_Monitoring_Plan.md` | Plugin Manager and plugin-driven monitoring |
| `Reports_Revision_Nagios_Alignment_Plan.md` | Reports page revision (#199) |
| `Service_Reports_Nagios_Availability_Plan.md` | Service reports from Nagios availability (#198) |
| `NAGIOS_CORE_FEATURE_GAP_PLAN.md` | The 2026-10-13 audit of Nagios Core features against Pinpoint, from which the 25 planned issues were written. Its status counts are out of date; all 25 issues shipped |

Still active and left in [`../../plans/`](../../plans/): only the plugin acceptance remediation list
(`Plugin_Driven_Monitoring_Remediation.md`).
