# Archived development issues (plan #1 to #25)

Engineering-ready tickets written on 2026-10-13 from
[`NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../plans/NAGIOS_CORE_FEATURE_GAP_PLAN.md). Each
`issue-NNN.md` is one plan issue with parts, acceptance criteria and deliverables.
[`INDEX.md`](INDEX.md) is the index, with the GitHub issue, status and pull requests for each plan
issue (audited in #303), and the plan-number to GitHub-number table.

**State (audited 2026-11-11, #303):** all 25 GitHub issues (#113 to #134, #153 to #156) are
closed, and the features exist in the code with tests (notification policy, contact groups and
escalations, parent devices, flap detection, event handlers and remediation, maintenance windows,
retry settings, storage and Nagios log, backup restore, bandwidth, plugin variables and SNMP v3,
NCPA hardening, manual NCPA registration, web check options, the command channel and
acknowledgements, forecasting, and the recovery toggle and safety controls).

Not complete, because the installer is a separate repo: implicit-TLS SMTP (#115 Part 2.1,
deferred) and the narrower `nagios` group rights for event handlers (#120, Handoff D1). The
journald size limit (#124 Part 11.1) is done in the installer repository. They are tracked in [`Installer_Handoff.md`](../plans/Installer_Handoff.md).
Availability targets (#134 Parts 21.2 and 21.3) were rejected by the owner.

Current behavior is in [`spec files/`](../../../spec%20files/) and
[`Implementation_Status.md`](../../../spec%20files/Implementation_Status.md), not here.
