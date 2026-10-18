# Modules 2–9 fixture plan

Issue: [#214](https://github.com/esfen14/Pinpoint/issues/214)

This is a preparation contract for the Module 2–9 queue. None of the states in
this plan has been verified on the appliance. The existing lab inspection proved
the served target and controlled baseline, not these case fixtures. Do not create
or alter a fixture until its exact operation, owner, evidence path, and recovery
are included in a reviewed card and the queue receives its separate start.

Fixture passwords belong in private same-owner files; never place values in this
file, a queue, a command line, a report, or a committed Playwright attachment.
Existing QA accounts or device records must be identified by exact reviewed
fixture identity before use. Similar-looking production or shared records are
not substitutes.

| Case | Required live fixture state | Preparation and recovery boundary |
|---|---|---|
| TC-ACC-10 | Super Admin; at least one active role; fewer than 99 existing accounts; two unique `example.invalid` addresses | The adapter creates two inactive accounts with alerts disabled. Rows and audit entries persist; this is not baseline restoration. E3 needs no active roles and remains blocked. |
| TC-ACC-08 | `qa-accounts` role with `account.view` and `account.edit` but no `account.alerts`; a user assigned to it | Create only through a reviewed account setup card. Preserve/deactivate the user and retain audit evidence; no direct database seeding. |
| TC-ROL-04 | `qa-view` role with only `system.dashboard`; a user assigned to it | Create through a reviewed role/account setup card. Verify the effective permission list before opening the case. |
| TC-DI-02 | One device with Monitored, Suggested, Stopped, and Archived ports | Read-only selection. Verify the device and each group before starting; do not change port state to satisfy the case. |
| TC-DI-03 | One Suggested port marked Held and Not used as intended, with expected/found names | Read-only selection. Verify exact port label and reason on the target before starting. |
| TC-DASH-07 | No ping check on any host and no NCPA host | Read-only baseline. Do not remove checks or deployments on the shared appliance to manufacture this state. |
| TC-NH-05 | Exactly one reporting ping host, then a second host with fresh reporting data | Requires a separately approved discovery/monitoring setup and wait for real data. Do not synthesize samples or claim a data horizon. |
| TC-NH-06 | SNMP device, monitored interface, traffic across all required ranges, and a no-interface device | Read-only selection. Require real observations in each range and a second device with no monitored interface. |
| TC-NH-07 | Host flap history and flap detection state spanning all requested date windows | Read-only selection. No synthetic flap rows or changed system clock. |
| TC-DI-05 | A monitored service that can be stopped and resumed | Mutating singleton case. Preserve current service/config state and prove restoration before any next case. |
| TC-DI-06 | Suggested unheld port, discoverable rescan target, and a plugin whose enabled state can be restored | Mutating case. Record exact plugin/port state before action and verify it after recovery. |
| TC-DI-07 | A monitored port and saved service name for boundary comparison | UI validation only; do not save a new service name. Preserve the original value. |
| TC-DI-08 | At least one TCP port and one UDP port | Read-only derived labels. Verify protocol/port identity before starting. |
| TC-DI-09 | A monitored service eligible for pinning, with current name and rescan state recorded | Mutating singleton case. Preserve the original name and verify it after unpin/rescan recovery. |
| TC-DI-11 | Hosts covering normal, paused, unknown address, missing, retired, merged, localhost, and precedence combinations | Read-only selection. Each required label must have an independently identified real row. |
| TC-DI-12 | Inventory rows covering the required monitoring labels and filter results | Read-only selection. Include enough rows to verify defaults, filters, and invalid GET without changing inventory. |
| TC-DI-13 | A normal monitored device with a successful rescan path, dashboard row, and event log | Mutating singleton case. Record monitoring/configuration state; pause, rescan, resume, then prove all original state is restored. |
| TC-DI-14 | Retired/merged, paused, and active devices | Read-only API/UI validation. Verify the case does not change any row. |
| TC-DI-15 | A paused device with a last known status | Read-only selection. Verify the device is excluded by default and included by the Paused filter. |
| TC-DI-16 | Empty and nonempty identity-review states plus searchable hostname | Read-only selection. Prior #164 reports remain partial. |
| TC-DI-17 | One unresolved identity review with two records and address history | Read-only selection. Do not merge, dismiss, or otherwise resolve the review. |
| TC-DI-18 | Two distinct identity records and users with different edit permissions | Read-only validation. Use exact pre-created accounts; do not modify roles during this case. |
| TC-DI-19 | Two disposable records eligible for merge | Irreversible singleton case with no undo. Do not run without a separately reviewed disposable appliance and explicit recovery approval. |
| TC-ACK-04 | Three active unacknowledged alerts, including an existing comment that must be preserved | Mutating case. Acknowledge only listed targets; any unacknowledgement/recovery operation needs its own reviewed action. |
| TC-ACK-07 | Same-severity acknowledged and unacknowledged alerts | Read-only selection. Verify the exact pair and preserve both states. |
| TC-ACK-08 | Isolated service that can be acknowledged, repaired, and safely faulted again | Disruptive singleton case. Requires a fault/recovery/re-fault plan with exact target and verified restoration. |
| TC-HIS-04 | History API data sufficient for valid and invalid date-range requests | Read-only API checks. Use existing data and record the actual default range; do not seed or edit history. |
| TC-DI-10 | Successfully deployed NCPA host with the protected NCPA port | Read-only check. Existing #129 report is partial; preserve it and verify current deployment state. |
| TC-DASH-09 | Three days of rising NCPA history, a new host with insufficient history, and a flat host | Read-only selection. The three-day horizon must be real and cannot be accelerated or fabricated. |
| TC-SS-05 | Same real forecast fixtures as TC-DASH-09, including rising and low-history services | Read-only selection. Verify metric source and history age before starting. |
| TC-DASH-06 | Saved refresh settings and a recoverable Nagios service/configuration baseline | Disruptive singleton case. Requires a separately reviewed service stop/restart and exact settings restoration plan. |

## Current fixture gate

The first batch's five complete adapters depend on these unverified states:

- TC-ACC-08: `qa-accounts` role and user.
- TC-ROL-04: `qa-view` role and user.
- TC-DI-02: a host with the required port lifecycle groups.
- TC-DI-03: a held mismatched Suggested port.
- TC-DASH-07: no ping checks and no NCPA host.

TC-ACC-10 is only partially mapped and cannot be accepted as a complete case.
The supervised module dispatcher accepts only TC-ACC-08, TC-ROL-04, TC-DI-02,
TC-DI-03, and TC-DASH-07, and only with complete source-bound cards, current
fixture/baseline proof, and an explicit start for the named queue set. It does
not create fixtures. TC-ACC-10 remains partial and excluded; the other 25 cases
remain unsupported. The five accepted cases are currently blocked because their
fixture states have not been verified. Setup actions and recovery must be added
to reviewed cards before any fixture is created.
