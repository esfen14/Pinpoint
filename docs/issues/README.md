# PinPoint Development Issues

These issues turn the gaps in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) into engineering-ready tasks. They were planned on 2026-10-13 and **none is implemented**.

## How to read the numbers

- `Issue #N` is the identifier from the feature-gap plan (§3). It is **not** a GitHub issue number. When an issue is filed on GitHub, record the GitHub number next to the plan identifier. Branches follow `.agent/workflows/work-issue.md` (`issue-<github number>-<slug>`).
- There is exactly one issue per plan number, so `Issue #N` here is plan issue #N. Work that touches several layers is split into labelled **Parts** inside the issue (for example `Part 19.2`), and each part keeps its own acceptance criteria.
- Part 14.1 (per-device plugin variables API) was added while writing these issues: the override it exposes is read by the config generator but nothing could write it.
- The availability-target part of issue #21 (Parts 21.2 and 21.3) is blocked until the team decides whether it wants targets.

## Title format

`<Component> <Work Type> <Description>`, where Component is `Web-Interface`, `System` or `Installer`, and Work Type is `Refinement` (extends something that exists) or `Implementation` (nothing exists yet).

## Index

| Issue | Title | Category | Priority | Dependencies |
|---|---|---|---|---|
| [Issue #1](issue-001.md) | System Implementation Add Configurable Notification Policy With Nagios Timeperiods and Settings Screen | System | High | None |
| [Issue #2](issue-002.md) | System Refinement Broaden Notification Mail Delivery Beyond Gmail and Report Failed Mail | System | Medium | None |
| [Issue #3](issue-003.md) | System Implementation Add Alert Contact Groups and Nagios Escalations With Management Screen | System | Medium | [Issue #1](issue-001.md) |
| [Issue #4](issue-004.md) | System Implementation Add Parent Device Relationships and Nagios Parents Rendering With Device Selector | System | Medium | None |
| [Issue #5](issue-005.md) | System Implementation Add Host-Based Service Notification Dependencies | System | Low | [Issue #4](issue-004.md) |
| [Issue #6](issue-006.md) | System Refinement Add Flap Detection Settings, Flapping Filter and Flap History | System | Medium | [Issue #10](issue-010.md) |
| [Issue #7](issue-007.md) | System Implementation Add Allowlisted Event Handler Framework With Remediation Screen and Installer Support | System | Medium | None |
| [Issue #8](issue-008.md) | System Implementation Add Local and Remote Service Recovery Actions With Restricted Sudo Rule | System | Low | [Issue #7](issue-007.md) |
| [Issue #9](issue-009.md) | System Implementation Add Maintenance Windows That Create Nagios Scheduled Downtime and a Management Page | System | High | [Issue #19](issue-019.md) |
| [Issue #10](issue-010.md) | System Refinement Add Retry Interval and Maximum Check Attempts Settings | System | Low | None |
| [Issue #11](issue-011.md) | System Refinement Set Journald Limit, Report Storage Usage and Add Nagios Log Tab | System | Low | None |
| [Issue #12](issue-012.md) | System Implementation Add Database Restore Command and Backup Health Reporting | System | Low | None |
| [Issue #13](issue-013.md) | System Implementation Add Interface Bandwidth Rates, Interface Discovery and Bandwidth Chart | System | Medium | [Issue #14](issue-014.md) |
| [Issue #14](issue-014.md) | System Implementation Add Per-Device Plugin Variables API and SNMP v3 Credential Support With Device Form | System | Medium | [Issue #16](issue-016.md) |
| [Issue #15](issue-015.md) | System Refinement Add Load Average, Swap and Disk I/O Defaults and Guided Process Check | System | Medium | None |
| [Issue #16](issue-016.md) | System Refinement Harden NCPA Deployment With Per-Device Port, Cleanup Action and Macro Secrets | System | Medium | None |
| [Issue #17](issue-017.md) | System Implementation Add Manual NCPA Agent Registration for Windows Hosts With Registration Form | System | Low | [Issue #16](issue-016.md) |
| [Issue #18](issue-018.md) | System Refinement Add POP3, IMAP and Expected-Response Options With Per-Device Web Check Form | System | Medium | [Issue #14](issue-014.md) |
| [Issue #19](issue-019.md) | System Implementation Add Nagios Command Channel, Acknowledgement Propagation and Check Now | System | High | None |
| [Issue #20](issue-020.md) | System Refinement Clear Acknowledgements on Recovery and Audit the History Page | System | Medium | None |
| [Issue #21](issue-021.md) | Web-Interface Refinement Reconcile Reports Documentation and Add Availability Target Support | Web-Interface | Low | None |
| [Issue #22](issue-022.md) | System Implementation Add Failure Escalation and Outcome Visibility for Automatic Recovery | System | Medium | [Issue #7](issue-007.md), [Issue #8](issue-008.md), [Issue #19](issue-019.md) |
| [Issue #23](issue-023.md) | Web-Interface Implementation Add Per-Service Recover Automatically Toggle With Restart Limit | Web-Interface | Low | [Issue #7](issue-007.md), [Issue #8](issue-008.md) |
| [Issue #24](issue-024.md) | System Implementation Add Remediation Safety Controls, Run Retention and Consumer Health Reporting | System | Medium | [Issue #7](issue-007.md) |
| [Issue #25](issue-025.md) | System Implementation Add Disk and Resource Trend Forecast Warnings From Stored Performance Data | System | Low | None (notifications need [Issue #19](issue-019.md), [Issue #22](issue-022.md)) |

## Totals

- **25 issues**: 9 Refinement and 16 Implementation.
- By category: Web-Interface 2, System 23, Installer 0.
- Issues #22 to #25 were added on 2026-10-13 to complete the proactive-recovery work started by Issues #7 and #8 (escalation, the per-service toggle, safety and health controls, and forecasting). Their parts are labelled in the same way.

## Blocked or conditional issues

| Issue | Why |
|---|---|
| [Issue #2](issue-002.md) | **Part 2.1 (Installer):** Conditional. Only needed if the team decides to support a relay that requires implicit TLS (port 465). STARTTLS relays work without any installer change. The helper is maintained in the installer repository, which is outside this repository, so the exact code location there is *further investigation required*. |
| [Issue #3](issue-003.md) | **Part 3.1 (System):** Coordinate with the already open GitHub issue #79 (per-host alert recipients). Do not start before #79's data model is decided, to avoid two competing recipient models. **Part 3.2 (Web-Interface):** Same condition as Part 3.1. |
| [Issue #4](issue-004.md) | **Part 4.1 (System):** Needs a scope decision first. `Implementation_Status.md` excludes backend topology computation and the topology view from the current release. Parent links (data and Nagios `parents` only, no map) are a different thing, but the team must confirm that before work starts. **Part 4.2 (Web-Interface):** Same condition as Part 4.1. |
| [Issue #5](issue-005.md) | Depends on Issue #4, which itself awaits a scope decision. |
| [Issue #7](issue-007.md) | **Part 7.1 (System):** Needs a security review of the design before coding, because it makes Nagios trigger actions. The execution model below (Nagios only records an event, PinPoint decides and runs an allowlisted action) is a proposal that must be confirmed on a lab appliance: spool directory permissions and who can read the spool were not verified. **Part 7.2 (Web-Interface):** Same condition as Part 7.1. **Part 7.3 (Installer):** Design to be confirmed with the security review of Part 7.1. Where the executable should live and its permissions on an installed appliance were not verified: the application directory is owned by another user and the `nagios` user may not be able to traverse it. |
| [Issue #8](issue-008.md) | **Part 8.1 (System):** Waits for the event handler framework (Issue #7). **Part 8.2 (Installer):** Waits for the security review of Issue #7. The installer code location is known (`setup/configure-pinpoint-privileges.sh` in the installer repository). **Part 8.3 (System):** Blocked by investigation. PinPoint has a deployment key and account on devices, but what the on-device sudo rule and helper allow was not verified, and an expanded rule on monitored devices is a security decision. |
| [Issue #11](issue-011.md) | **Part 11.1 (Installer):** The installer code location is not in this repository, *further investigation required*. |
| [Issue #12](issue-012.md) | Covers a documented cold-standby recovery only. Active/passive failover (two live nodes, duplicate-check prevention, split-brain handling) is not planned here and needs its own architecture decision, because PinPoint uses SQLite and an in-process scheduler on one host. |
| [Issue #17](issue-017.md) | **Part 17.1 (System):** Needs a scope decision on Windows hosts, and NCPA's Windows API paths (disk and process names differ from Linux) must be probed on a lab Windows host first. NRPE is out of scope by team decision. **Part 17.2 (Web-Interface):** Same condition as Part 17.1. |
| [Issue #22](issue-022.md) | Waits for Issue #7 and the command channel in Issue #19. Whether Nagios on the appliance accepts custom notification external commands is *further investigation required*. |
| [Issue #23](issue-023.md) | Waits for Issue #7 and Part 8.1. Remote services also wait for Part 8.3 (blocked by investigation). |
| [Issue #24](issue-024.md) | Kill switch, retention and health can start after Issue #7. The acknowledgement check waits for Issue #19 and the downtime check for Issue #9. |
| [Issue #25](issue-025.md) | **Awaiting a product decision.** Forecasting goes beyond Nagios Core, and the team must confirm it wants it and whether it may notify. Do not start until decided. |
| [Issue #21](issue-021.md) | **Part 21.2 (System):** **Awaiting a product decision.** An availability target (a percentage that uptime is compared against) goes beyond Nagios Core, which only reports measured percentages. Do not start until the team confirms it wants targets. Scheduled or recurring reports by email are not planned here and would depend on Issue #2. **Part 21.3 (Web-Interface):** Same condition as Part 21.2. |

## Suggested order

1. Foundations: [Issue #19](issue-019.md) (Nagios command channel), [Issue #1](issue-001.md) (notification policy), [Issue #10](issue-010.md) (check timing), [Issue #14](issue-014.md) (per-device plugin variables), [Issue #16](issue-016.md) (secrets and NCPA port).
2. Features that need the foundations: [Issue #9](issue-009.md) (downtime), [Issue #3](issue-003.md) (escalations), [Issue #6](issue-006.md) (flap settings), [Issue #7](issue-007.md) (event handlers).
3. Independent issues can run in parallel with any step: #2, #11, #12, #13, #15, #18, #20 and Part 21.1.
4. Proactive recovery chain: #7, then #8, then #24 (safety controls before any action is enabled in production), then #22 and #23. #25 is independent but needs a product decision.
5. Anything marked blocked waits for its decision.

## Rules that apply to every issue

- Work in a branch and pull request per `.agent/workflows/work-issue.md`, and finish with `scripts/verify.sh`.
- A pull request needs the acceptance criteria, deliverables and merge requirements in its issue. Evidence must be attached, never assumed.
- No issue may weaken or skip an existing test.

## GitHub numbers

Plan identifiers are not GitHub numbers. Branches use the GitHub number (`issue-<number>-<slug>`).

| Plan | GitHub | Plan | GitHub | Plan | GitHub |
|---|---|---|---|---|---|
| #1 | #113 | #10 | #123 | #19 | #132 |
| #2 | #115 | #11 | #124 | #20 | #133 |
| #3 | #116 | #12 | #125 | #21 | #134 |
| #4 | #117 | #13 | #126 | #22 | #153 |
| #5 | #118 | #14 | #127 | #23 | #154 |
| #6 | #119 | #15 | #128 | #24 | #155 |
| #7 | #120 | #16 | #129 | #25 | #156 |
| #8 | #121 | #17 | #130 | | |
| #9 | #122 | #18 | #131 | | |
