# PinPoint Development Issues

These issues turn the gaps in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) into engineering-ready tasks. They were planned on 2026-10-13 and **none is implemented**.

## How to read the numbers

- `Issue #N` is the identifier from the feature-gap plan (§3). It is **not** a GitHub issue number. When an issue is filed on GitHub, record the GitHub number next to the plan identifier. Branches follow `.agent/workflows/work-issue.md` (`issue-<github number>-<slug>`).
- `Issue #N.M` is an independently deliverable sub-issue of plan issue #N. Issue #N alone has no file when it was split.
- Plan issue numbers are unchanged. The availability-target part of plan issue #21 (sub-issues #21.2 and #21.3) is blocked until the team decides whether it wants targets; #21.1 is independent.
- Sub-issue #14.1 (per-device plugin variables API) was added while writing these issues: the override it exposes is read by the config generator but nothing could write it.

## Title format

`<Component> <Work Type> <Description>`, where Component is `Web-Interface`, `System` or `Installer`, and Work Type is `Refinement` (extends something that exists) or `Implementation` (nothing exists yet).

## Index

| Issue | Title | Category | Priority | Dependencies |
|---|---|---|---|---|
| [Issue #1.1](issue-001-1.md) | System Implementation Add Notification Policy Model and Nagios Timeperiod Rendering | System | High | None |
| [Issue #1.2](issue-001-2.md) | Web-Interface Refinement Add Notification Policy Settings and Correct the Notifications Toggle Label | Web-Interface | High | [Issue #1.1](issue-001-1.md) |
| [Issue #2.1](issue-002-1.md) | Installer Refinement Allow Implicit TLS in the SMTP Helper for Non-Gmail Relays | Installer | Medium | None |
| [Issue #2.2](issue-002-2.md) | System Refinement Allow Generic SMTP Relay and Report Failed Notification Mail | System | Medium | [Issue #2.1](issue-002-1.md) (only for implicit TLS) |
| [Issue #2.3](issue-002-3.md) | Web-Interface Refinement Add Relay Selection and Mail Failure Notice to Email Settings | Web-Interface | Medium | [Issue #2.2](issue-002-2.md) |
| [Issue #3.1](issue-003-1.md) | System Implementation Add Alert Contact Groups and Nagios Escalation Rendering | System | Medium | [Issue #1.1](issue-001-1.md) |
| [Issue #3.2](issue-003-2.md) | Web-Interface Implementation Add Escalation Management Screen | Web-Interface | Medium | [Issue #3.1](issue-003-1.md) |
| [Issue #4.1](issue-004-1.md) | System Implementation Add Parent Device Relationships and Nagios Parents Rendering | System | Medium | None |
| [Issue #4.2](issue-004-2.md) | Web-Interface Refinement Add Parent Device Selector to Device Inventory | Web-Interface | Medium | [Issue #4.1](issue-004-1.md) |
| [Issue #5](issue-005.md) | System Implementation Add Host-Based Service Notification Dependencies | System | Low | [Issue #4.1](issue-004-1.md) |
| [Issue #6.1](issue-006-1.md) | System Refinement Add Flap Detection Settings and Flap History Reporting | System | Medium | [Issue #10](issue-010.md) |
| [Issue #6.2](issue-006-2.md) | Web-Interface Refinement Add Flap Detection Settings Card and Flapping History View | Web-Interface | Medium | [Issue #6.1](issue-006-1.md) |
| [Issue #7.1](issue-007-1.md) | System Implementation Add Allowlisted Event Handler Framework with Remediation Audit Log | System | Medium | [Issue #7.3](issue-007-3.md) |
| [Issue #7.2](issue-007-2.md) | Web-Interface Implementation Add Remediation Actions Screen and Run Log | Web-Interface | Medium | [Issue #7.1](issue-007-1.md) |
| [Issue #7.3](issue-007-3.md) | Installer Implementation Install Event Handler Spool Directory and Handler Executable | Installer | Medium | None |
| [Issue #8.1](issue-008-1.md) | System Implementation Add Local Service Restart Action Type for Service Recovery | System | Low | [Issue #7.1](issue-007-1.md); [Issue #8.2](issue-008-2.md) |
| [Issue #8.2](issue-008-2.md) | Installer Implementation Add Restricted Sudo Rule for Allowlisted Local Service Restarts | Installer | Low | None |
| [Issue #8.3](issue-008-3.md) | System Implementation Add Remote Service Restart Through the NCPA Deployment Account | System | Low | [Issue #7.1](issue-007-1.md); [Issue #8.1](issue-008-1.md) |
| [Issue #9.1](issue-009-1.md) | System Implementation Add Maintenance Windows That Create Nagios Scheduled Downtime | System | High | [Issue #19.1](issue-019-1.md) |
| [Issue #9.2](issue-009-2.md) | Web-Interface Implementation Add Maintenance Windows Page | Web-Interface | High | [Issue #9.1](issue-009-1.md) |
| [Issue #10](issue-010.md) | System Refinement Add Retry Interval and Maximum Check Attempts Settings | System | Low | None |
| [Issue #11.1](issue-011-1.md) | Installer Refinement Set an Explicit Journald Size Limit for PinPoint Logs | Installer | Low | None |
| [Issue #11.2](issue-011-2.md) | System Refinement Add Log and Database Storage Usage and a Read-Only Nagios Log Route | System | Low | None |
| [Issue #11.3](issue-011-3.md) | Web-Interface Refinement Show Storage Usage and Add a Nagios Log Tab to System Logs | Web-Interface | Low | [Issue #11.2](issue-011-2.md) |
| [Issue #12](issue-012.md) | System Implementation Add Database Restore Command and Backup Health Reporting | System | Low | None |
| [Issue #13.1](issue-013-1.md) | System Implementation Add Interface Bandwidth Rate Calculation and Interface Discovery | System | Medium | [Issue #14.1](issue-014-1.md) |
| [Issue #13.2](issue-013-2.md) | Web-Interface Refinement Add Interface Selector and Bandwidth Chart to Network Health | Web-Interface | Medium | [Issue #13.1](issue-013-1.md) |
| [Issue #14.1](issue-014-1.md) | System Implementation Add Per-Device Plugin Variables API | System | Medium | None |
| [Issue #14.2](issue-014-2.md) | System Refinement Add SNMP Version Choice and v3 Credential Support | System | Medium | [Issue #14.1](issue-014-1.md); [Issue #16.4](issue-016-4.md) |
| [Issue #14.3](issue-014-3.md) | Web-Interface Refinement Add Per-Device SNMP Version and Credential Form | Web-Interface | Medium | [Issue #14.2](issue-014-2.md) |
| [Issue #15.1](issue-015-1.md) | System Refinement Add Load Average, Swap and Disk I/O NCPA Defaults | System | Medium | None |
| [Issue #15.2](issue-015-2.md) | Web-Interface Refinement Add Guided Process Check Entry to Plugin Settings | Web-Interface | Low | [Issue #15.1](issue-015-1.md) |
| [Issue #16.1](issue-016-1.md) | System Refinement Track the Deployed NCPA Port Per Device | System | Medium | None |
| [Issue #16.2](issue-016-2.md) | System Implementation Add NCPA Deployment Cleanup Action | System | Medium | None |
| [Issue #16.3](issue-016-3.md) | Web-Interface Refinement Add Cleanup Action to NCPA Deployment History | Web-Interface | Medium | [Issue #16.2](issue-016-2.md) |
| [Issue #16.4](issue-016-4.md) | System Refinement Move Check Secrets From Command Lines Into Nagios Resource Macros | System | Medium | None |
| [Issue #17.1](issue-017-1.md) | System Implementation Add Manual NCPA Agent Registration for Windows Hosts | System | Low | [Issue #16.1](issue-016-1.md) |
| [Issue #17.2](issue-017-2.md) | Web-Interface Refinement Add Manual NCPA Registration and Windows Instructions to NCPA Deployment | Web-Interface | Low | [Issue #17.1](issue-017-1.md) |
| [Issue #18.1](issue-018-1.md) | System Refinement Add POP3, IMAP and Expected-Response Options to Mail and Web Service Checks | System | Medium | [Issue #14.1](issue-014-1.md) |
| [Issue #18.2](issue-018-2.md) | Web-Interface Refinement Add Per-Device Web Check Options Form | Web-Interface | Medium | [Issue #18.1](issue-018-1.md); [Issue #14.1](issue-014-1.md) |
| [Issue #19.1](issue-019-1.md) | System Implementation Add Nagios Command Channel and Propagate Acknowledgements to Nagios | System | High | None |
| [Issue #19.2](issue-019-2.md) | System Implementation Add Check Now Routes Through the Nagios Command Channel | System | Medium | [Issue #19.1](issue-019-1.md) |
| [Issue #19.3](issue-019-3.md) | Web-Interface Refinement Add Check Now Button and Nagios Acknowledgement Status Indicator | Web-Interface | Medium | [Issue #19.1](issue-019-1.md); [Issue #19.2](issue-019-2.md) |
| [Issue #20.1](issue-020-1.md) | System Refinement Clear Acknowledgements on Recovery and Record AUTO_RESOLVED History | System | Medium | None |
| [Issue #20.2](issue-020-2.md) | Web-Interface Refinement Audit History Page Against Requirements and Fix Gaps | Web-Interface | Medium | None |
| [Issue #21.1](issue-021-1.md) | Web-Interface Refinement Reconcile Reports Page Documentation With Implemented Report Views | Web-Interface | Low | None |
| [Issue #21.2](issue-021-2.md) | System Implementation Add Availability Target Setting and Breach Flag to Availability Report | System | Low | [Issue #21.1](issue-021-1.md) |
| [Issue #21.3](issue-021-3.md) | Web-Interface Refinement Add Availability Target Control and Breach Indicator to Reports | Web-Interface | Low | [Issue #21.2](issue-021-2.md) |

## Totals

- **48 issues**: 27 Refinement and 21 Implementation.
- By category: Web-Interface 18, System 26, Installer 4.

## Blocked or conditional issues

| Issue | Why |
|---|---|
| [Issue #2.1](issue-002-1.md) | Conditional. Only needed if the team decides to support a relay that requires implicit TLS (port 465). STARTTLS relays work without any installer change. The helper is maintained in the installer repository, which is outside this repository, so the exact code location there is *further investigation required*. |
| [Issue #3.1](issue-003-1.md) | Coordinate with the already open GitHub issue #79 (per-host alert recipients). Do not start before #79's data model is decided, to avoid two competing recipient models. |
| [Issue #3.2](issue-003-2.md) | Same condition as Issue #3.1. |
| [Issue #4.1](issue-004-1.md) | Needs a scope decision first. `Implementation_Status.md` excludes backend topology computation and the topology view from the current release. Parent links (data and Nagios `parents` only, no map) are a different thing, but the team must confirm that before work starts. |
| [Issue #4.2](issue-004-2.md) | Same condition as Issue #4.1. |
| [Issue #5](issue-005.md) | Depends on Issue #4.1, which itself awaits a scope decision. |
| [Issue #7.1](issue-007-1.md) | Needs a security review of the design before coding, because it makes Nagios trigger actions. The execution model below (Nagios only records an event, PinPoint decides and runs an allowlisted action) is a proposal that must be confirmed on a lab appliance: spool directory permissions and who can read the spool were not verified. |
| [Issue #7.2](issue-007-2.md) | Same condition as Issue #7.1. |
| [Issue #7.3](issue-007-3.md) | Design to be confirmed with the security review of Issue #7.1. Where the executable should live and its permissions on an installed appliance were not verified: the application directory is owned by another user and the `nagios` user may not be able to traverse it. |
| [Issue #8.1](issue-008-1.md) | Waits for the event handler framework (Issue #7.1). |
| [Issue #8.2](issue-008-2.md) | Wait for the security review of Issue #7.1. The installer code location is not in this repository, *further investigation required*. |
| [Issue #8.3](issue-008-3.md) | Blocked by investigation. PinPoint has a deployment key and account on devices, but what the on-device sudo rule and helper allow was not verified, and an expanded rule on monitored devices is a security decision. |
| [Issue #11.1](issue-011-1.md) | The installer code location is not in this repository, *further investigation required*. |
| [Issue #12](issue-012.md) | Covers a documented cold-standby recovery only. Active/passive failover (two live nodes, duplicate-check prevention, split-brain handling) is not planned here and needs its own architecture decision, because PinPoint uses SQLite and an in-process scheduler on one host. |
| [Issue #17.1](issue-017-1.md) | Needs a scope decision on Windows hosts, and NCPA's Windows API paths (disk and process names differ from Linux) must be probed on a lab Windows host first. NRPE is out of scope by team decision. |
| [Issue #17.2](issue-017-2.md) | Same condition as Issue #17.1. |
| [Issue #21.2](issue-021-2.md) | **Awaiting a product decision.** An availability target (a percentage that uptime is compared against) goes beyond Nagios Core, which only reports measured percentages. Do not start until the team confirms it wants targets. Scheduled or recurring reports by email are not planned here and would depend on Issue #2.2. |
| [Issue #21.3](issue-021-3.md) | Same condition as Issue #21.2. |

## Suggested order

1. Foundations: [Issue #19.1](issue-019-1.md) (Nagios command channel), [Issue #1.1](issue-001-1.md) (notification policy), [Issue #10](issue-010.md) (check timing), [Issue #6.1](issue-006-1.md) (flap settings).
2. Features that need the foundations: [Issue #9.1](issue-009-1.md) (downtime), [Issue #3.1](issue-003-1.md) (escalations), [Issue #7.1](issue-007-1.md) (event handlers).
3. Independent refinements can run in parallel with any step: #2.x, #11.x, #13.x, #14.x, #15.x, #16.x, #18, #20.x, #21.1.
4. Anything marked blocked waits for its decision.

## Rules that apply to every issue

- Work in a branch and pull request per `.agent/workflows/work-issue.md`, and finish with `scripts/verify.sh`.
- A pull request needs the acceptance criteria, deliverables and merge requirements in its issue. Evidence must be attached, never assumed.
- No issue may weaken or skip an existing test.
