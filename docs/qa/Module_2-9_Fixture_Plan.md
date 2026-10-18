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
| TC-DI-08 | One preexisting non-archived editable TCP port with `http` in service options and one preexisting non-archived editable UDP port on the reviewed device | Read-only dialog checks. Adapter blocks any port PUT and cancels both dialogs; verify exact labels, Set service actions, and service options before start. |
| TC-DI-07 | Two preexisting non-archived editable ports on the reviewed device: one whose service is not `ssh`, and one whose service is exactly `ssh` | Read-only validation checks. Adapter blocks any port PUT and cancels both dialogs; verify labels, current names, and Set service actions before start. |
| TC-DASH-07 | No ping check on any host and no NCPA host | Read-only baseline. Do not remove checks or deployments on the shared appliance to manufacture this state. |
| TC-NH-05 | Exactly one reporting ping host, then a second host with fresh reporting data | Requires a separately approved discovery/monitoring setup and wait for real data. Do not synthesize samples or claim a data horizon. |
| TC-NH-06 | SNMP device, monitored interface, traffic across all required ranges, and a no-interface device | Read-only selection. Require real observations in each range and a second device with no monitored interface. |
| TC-NH-07 | Host flap history and flap detection state spanning all requested date windows | Read-only selection. No synthetic flap rows or changed system clock. |
| TC-DI-05 | A monitored service that can be stopped and resumed | Mutating singleton case. Preserve current service/config state and prove restoration before any next case. |
| TC-DI-06 | Suggested unheld port, discoverable rescan target, and a plugin whose enabled state can be restored | Mutating case. Record exact plugin/port state before action and verify it after recovery. |
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
| TC-HIS-04 | Super Admin with `system.history`; at least one real alert event older than 25 hours but within the rolling 30-day history | Read-only GETs only. Adapter compares the existing event with a no-date response; if no qualifying event exists, E3 stays blocked. Do not seed or edit history. |
| TC-DI-10 | Successfully deployed NCPA host with the protected NCPA port | Read-only check. Existing #129 report is partial; preserve it and verify current deployment state. |
| TC-DASH-09 | Three days of rising NCPA history, a new host with insufficient history, and a flat host | Read-only selection. The three-day horizon must be real and cannot be accelerated or fabricated. |
| TC-SS-05 | Same real forecast fixtures as TC-DASH-09, including rising and low-history services | Read-only selection. Verify metric source and history age before starting. |
| TC-DASH-06 | Saved refresh settings and a recoverable Nagios service/configuration baseline | Disruptive singleton case. Requires a separately reviewed service stop/restart and exact settings restoration plan. |

## Current fixture gate

### 2026-10-18 execution-readiness check

At `2026-10-18T12:29:16.826139Z`, the supported read-only `qa_pilot.py inspect`
verified the controlled runtime baseline for lab
`351eb491-f5e1-4854-a7e4-68309ad774ad`, target
`299ab3ba7203c89a3ca5d8fabea42d9e5f239be2`, and baseline checksum
`da42da6cdbc38dab7ba6f9d96c2abd9cfb822123429fdd3f1e613ea50f8e07c3`.
This is environment evidence only; it is not a case run or authorization.
The private inspection is stored outside the repository. The approved private
fixture-input files for the two QA accounts and the device/port labels were
absent at inspection time. No credential values were read, and no accounts,
roles, ports, alerts, or other appliance records were created or changed.

Queue v12, `2026-10-18-modules-2-9-adapters-v12.json`, splits the seven exact
IDs into two runner-compatible named sets: set 01 has five cases in one batch;
set 02 has two cases in one batch. Each card now binds its source adapter,
per-case timeout, expected-item evidence path, private control/bridge paths,
container image, baseline hash and recovery instructions. Each card explicitly
records `case_fixtures: UNVERIFIED`, so the set remains blocked.

| Case | Fixture evidence still required before its set can start |
|---|---|
| TC-ACC-08 | Confirm the pre-created `qa-accounts` role grants account.view and account.edit but not account.alerts, assigned user exists, and both users' private credentials are available. |
| TC-ROL-04 | Confirm the pre-created `qa-view` account has only system.dashboard among protected page/API permissions and its private credentials are available. |
| TC-DI-02 | Identify the exact existing device and independently observe Monitored, Suggested, Stopped, and Archived ports and their expected ordering data. |
| TC-DI-03 | Identify an exact existing Suggested port that is held, marked Not used as intended, with the expected/found mismatch and unacknowledged state visible. |
| TC-DASH-07 | Observe that no host has a ping check and no NCPA host/data is present. Do not remove checks or deployments to manufacture this state. |
| TC-DI-08 | Identify exact existing editable, non-archived TCP and UDP port labels on the reviewed device; prove TCP options include `http`. |
| TC-HIS-04 | Confirm Super Admin has system.history and capture the identifier/time of a real alert event older than 25 hours but within the rolling 30-day range, without modifying history. |

After the fixture facts are collected, update the private input files and the
matching card's fixture status, then refresh/review the queue hashes and
preflight immediately before start. Cases that cannot meet a prerequisite stay
blocked; do not create or mutate shared appliance state as an improvised setup.
The two named sets require separate explicit starts under the shared workflow.

### Creation feasibility for the requested fixtures

The current supervised pilot launches only the seven case adapters; it has no
fixture-provisioning action. Do not create records by direct SQL, API calls,
shell commands, or a host browser to get around that boundary.

| Fixture | Can it be created safely for this run? | Reason / required path |
|---|---|---|
| `qa-accounts` role and user (TC-ACC-08) | Only after setup support and a reviewed setup start | UI creation is possible in the product, but the role/user and login audit entries persist. The adapter only observes them and will not create, edit, or deactivate them. Use a disposable isolated QA appliance or explicitly accept these persistent records in a reviewed setup card. |
| `qa-view` role and user (TC-ROL-04) | Only after setup support and a reviewed setup start | Same persistence boundary; permissions must be independently verified before the case. Do not adjust an existing role or account. |
| Lifecycle port groups and held mismatch (TC-DI-02/03) | Must be observed on an existing fixture host or built in an isolated appliance | Port states come from discovery/monitoring data. Creating them would need network discovery and port lifecycle mutations, neither supported by this read-only run. Never repurpose a real/shared device. |
| TCP/UDP service options (TC-DI-08) | Usually observed, not seeded | Select existing editable, non-archived ports on a reviewed fixture host. The case adapter blocks port writes and cancels dialogs. If none match, prepare a disposable host with real listeners in a separate reviewed lab setup. |
| No ping and no NCPA (TC-DASH-07) | Cannot be manufactured safely in the current shared lab | This is a negative environment property. Removing monitoring checks or deployments would alter appliance state and is prohibited by this run. It must already be true on the selected appliance. |
| Qualifying alert history (TC-HIS-04) | Cannot be manufactured for this run | The requirement is a real alert event older than 25 hours within the rolling 30 days. Do not insert/edit history timestamps or change the clock; select a naturally qualifying event or wait for one. |

Therefore a single “create all fixtures” operation is not available. To make
the whole seven-case queue runnable, use an isolated QA appliance prepared with
the role/account and real port fixtures, and verify that its dashboard/history
already satisfy the two environment-dependent cases. Otherwise only the cases
whose existing fixtures can be proved are eligible; missing fixture cases stay
blocked. No snapshot is needed just to run the read-only cases, but fixture
provisioning on the shared lab must be treated as a separate state-changing
setup with its own recovery and approval.

The first batch contains four complete adapters and partial TC-ACC-10; the complete adapters depend on these unverified states:

- TC-ACC-08: `qa-accounts` role and user.
- TC-ROL-04: `qa-view` role and user.
- TC-DI-02: a host with the required port lifecycle groups.
- TC-DI-03: a held mismatched Suggested port.
- TC-DASH-07: no ping checks and no NCPA host.

TC-ACC-10 is only partially mapped and cannot be accepted as a complete case.
The supervised module dispatcher accepts only TC-ACC-08, TC-ROL-04, TC-DI-02,
TC-DI-03, TC-DI-08, TC-HIS-04, and TC-DASH-07, and only with complete source-bound cards, current
fixture/baseline proof, and an explicit start for the named queue set. It does
not create fixtures. Of the 24 cases outside its allowlist, TC-ACC-10 remains
partial, TC-DI-07 is source-complete but blocked on the uppercase expectation
mismatch and failure-result handling, and 22 remain unmapped. The seven accepted cases are currently blocked because their
fixture states have not been verified. Setup actions and recovery must be added
to reviewed cards before any fixture is created.
