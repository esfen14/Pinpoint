# Modules 2–9 current-case adapter review

Issue: [#214](https://github.com/esfen14/Pinpoint/issues/214)

This review maps the 31 catalog cases still listed as Not run after excluding
TC-ACC-09 and TC-SS-04, whose separate supervised reports record PASS. Source
coverage is a statement about reviewed test code; it does not indicate that an
appliance is ready, a case ran, or a live launcher accepts the case.

## Completed cases excluded from this queue

| Case | Current report result | Tested target | Expected items accepted | Report |
|---|---|---|---|---|
| TC-ACC-09 | PASS; restoration and baseline accepted | `299ab3ba7203c89a3ca5d8fabea42d9e5f239be2` | E1, E2 | [2026-10-18 next permissions](../test-runs/2026-10-18-next-permissions/REPORT.md) |
| TC-SS-04 | PASS; restoration and baseline accepted | `299ab3ba7203c89a3ca5d8fabea42d9e5f239be2` | E1 | [2026-10-18 SS-04 recheck](../test-runs/2026-10-18-issue-211-ss04-recheck/REPORT.md) |

The new Module 2–9 queue selects 31 other catalog cases and contains neither
ID. The catalog's historical `Result` cells and the generated source/result
view remain `Not run` by design: the workflow preserves original human entries
and records new executions in attributable reports. These linked reports are
the current execution record for these two cases; do not rerun them as untested.

## Case-by-case assessment

| Case | Expected items | Primary source and focused local tests | Prerequisite / mutation / recovery concern |
|---|---:|---|---|
| TC-ACC-10 | 3 | `ManageAccountsPage.tsx`; `ManageAccountsPage.test.tsx` | Partial adapter covers E1/E2. Needs an active role, a fresh run token, and a disposable appliance; creates two inactive accounts with alerts disabled. Rows/audit entries persist, so cleanup is not baseline restoration. E3 would require removing all active role options and remains blocked. A partial #191 browser report remains partial evidence. |
| TC-ACC-08 | 2 | `ManageAccountsPage.tsx`, `ManageRolesPage.tsx`; account/role page tests | Requires pre-created `qa-accounts` role and user. Read-only UI checks across Super Admin and restricted account sessions. |
| TC-ROL-04 | 3 | `ManageRolesPage.tsx`, `Sidebar.tsx`, `pageAccess.ts`; role/access tests | Requires a `qa-view` account. Iterates 13 pages and three APIs; needs separate restricted credentials and exact redirects/403s. |
| TC-DI-02 | 3 | `DevicePortsSection.tsx`, `devicePortsLogic.ts`; `DevicePortsSection.test.tsx` | Requires one device with ports in multiple lifecycle groups. Read-only; environment must provide each required state. |
| TC-DI-03 | 2 | `DevicePortsSection.tsx`, `devicePortsLogic.ts`; port component/logic tests | Requires a Suggested port that is both held and not-as-intended. Read-only; exact precedence/text needs a matching real record. |
| TC-DI-08 | 4 | `SetServiceDialog.tsx`, `devicePortsLogic.ts`, `DevicePortsSection.tsx`; service and port component tests | Requires reviewed existing TCP and UDP ports on one device. A network route guard aborts any attempted port PUT; both dialogs are canceled without saving. |
| TC-DI-07 | 3 | `SetServiceDialog.tsx`, `devicePortsLogic.ts`, `DevicePortsSection.tsx`; device port logic/component tests | Requires one editable port not already named `ssh` and a second editable port named `ssh`. Adapter blocks every port PUT and cancels both dialogs. The procedure says uppercase `SSH` is invalid; the component lowercases before validation, so E2 is a deliberate compatibility check that may expose an implementation/spec discrepancy, not an assumed PASS. |
| TC-DASH-07 | 2 | `DashboardPage.tsx`, dashboard metric components; `DashboardPage.test.tsx` | Requires no ping checks and no NCPA host. Read-only only after this baseline is independently observed. |
| TC-NH-05 | 2 | `NetworkHealthPage.tsx`, summary/trend components; `NetworkHealthPage.test.tsx` | Requires exactly one reporting ping host then a second host with new data. Adding a check and waiting changes lab config; no adapter may manufacture that evidence. |
| TC-NH-06 | 3 | `BandwidthCard.tsx`, `BandwidthChart.tsx`; `BandwidthCard.test.tsx` | Requires an SNMP device with monitored interface, traffic readings across four ranges, plus no-interface state. Read-only if fixture is already prepared. |
| TC-NH-07 | 3 | `FlapHistorySection.tsx`, `HostTable.tsx`, `DeviceInventoryPage.tsx`; inventory tests | Requires host flap history and flap-detection state. Read-only; four date windows and filtering need suitable real history. |
| TC-DI-05 | 4 | `DevicePortsSection.tsx`, `devicePortsLogic.ts`; `DevicePortsSection.test.tsx`, `devicePortsApi.test.ts` | Stops and resumes a monitored service. Reversible but changes Nagios config/state; verify service absence/return and restoration before continuing. Singleton batch. |
| TC-DI-06 | 2 | `DevicePortsSection.tsx`, device port API; `DevicePortsSection.test.tsx` | Holds a Suggested port, rescans, then disables/enables a plugin. Mutates discovery and monitoring configuration; needs a scoped target and verified restore. |
| TC-DI-09 | 3 | `DevicePortsSection.tsx`, `devicePortsLogic.ts`; device port tests | Pins and removes a service pin, then rescans. Changes service naming/config and needs preserved prior name plus rescan/recovery proof. Singleton batch. |
| TC-DI-11 | 3 | `DeviceMonitoringSection.tsx`, `monitoringState.ts`; `DeviceMonitoringState.test.tsx` | Requires normal, paused, address-unknown, missing, retired, merged, localhost, and precedence-combination rows. Read-only with prepared inventory. |
| TC-DI-12 | 3 | `DeviceInventoryPage.tsx`, `HostTable.tsx`, monitoring API; inventory tests | Checks default/filter values and an invalid GET. Read-only; host records must cover each monitoring label. |
| TC-DI-13 | 4 | `DeviceMonitoringSection.tsx`, `HostTable.tsx`, `DeviceInventoryPage.tsx`; monitoring tests | Pauses, rescans, resumes a device, and reads Dashboard/logs. Changes monitoring and Nagios configuration; singleton batch with restoration proof. |
| TC-DI-14 | 2 | `DeviceMonitoringSection.tsx`, monitoring API; inventory tests | Requires retired/merged, paused, and active devices. UI/API checks should be non-mutating and prove no state changed. |
| TC-DI-15 | 3 | `HostTable.tsx`, `DeviceInventoryPage.tsx`; inventory tests | Requires a paused device. Read-only; verify default Monitored view, Paused filter, last-known-status label, monitored-only summary. |
| TC-DI-16 | 2 | `DeviceIdentityReviews.tsx`, `DeviceInventoryPage.tsx`; `DeviceIdentityReview.test.tsx` | Needs empty and nonempty review states plus a hostname search. Read-only. Earlier #164 browser reports are partial; current UI/source compatibility still needs fresh execution. |
| TC-DI-17 | 3 | `IdentityReviewDrawer.tsx`, `DeviceIdentityReviews.tsx`; identity review tests | Requires unresolved review with two records and address history. Read-only; verify history is loaded only on button press and close does not write. Prior partial reports remain partial. |
| TC-DI-18 | 3 | `IdentityReviewDrawer.tsx`, permissions; identity review tests | Needs two distinct records and two roles with different edit permission. Read-only validation, but requires multiple authenticated identities. Prior report is partial. |
| TC-DI-19 | 3 | `IdentityReviewDrawer.tsx`, device identity API; identity review tests | Performs an irreversible merge with no undo. Must not be run without a separately reviewed disposable fixture and restoration plan; singleton treatment needs review. Prior report is partial. |
| TC-ACK-04 | 2 | `DashboardPage.tsx`, `RecentOutageTable.tsx`, acknowledgement modal; dashboard tests | Requires three active unacknowledged alerts, then writes acknowledgements. Must preserve an existing comment and prove all intended items; unacknowledge/recovery actions need a separately approved recovery plan. |
| TC-ACK-07 | 1 | `RecentOutageTable.tsx`, `DashboardPage.tsx`; dashboard tests | Requires same-severity acknowledged and unacknowledged alerts. Read-only once state exists. |
| TC-ACK-08 | 3 | Dashboard acknowledgement flow and History; dashboard/history tests | Acknowledges, repairs, then breaks a target again. Fault/recovery/re-fault is disruptive and must be isolated with explicit recovery; singleton batch. |
| TC-HIS-04 | 3 | `history.py`, History API client/page; `HistoryPage.test.tsx` | Read-only GETs verify valid/invalid ranges. E3 compares a real event older than 25 hours in the rolling 30-day range against a no-date response; if no such event exists, E3 is blocked rather than inferred from an empty response. |
| TC-DI-10 | 2 | `DevicePortsSection.tsx`, NCPA deployment/port API; inventory tests | Requires successful NCPA deployment. Read-only but a prior #129 report is partial and relevant source paths changed; preserve as partial and do not infer a pass. |
| TC-DASH-09 | 5 | `ForecastList.tsx`, `useForecasts.ts`, forecast types; forecast/dashboard tests | Requires three days of rising NCPA history, new host with insufficient history, and a flat host. Read-only display; data horizon cannot be fabricated or accelerated in a live run. |
| TC-SS-05 | 2 | `SystemStatusPage.tsx`, `ServiceStatusTable.tsx`, forecast types; service-status tests | Requires the same forecast fixtures as TC-DASH-09. Read-only display; verify a real rising metric and a low-history service. |
| TC-DASH-06 | 2 | `DashboardPage.tsx`, refresh settings and service overview; dashboard/settings tests | Changes refresh settings, stops and restarts Nagios. Privileged disruptive action; requires separately reviewed stop/recovery and restoration proof. Singleton batch. |

## Adapter and execution boundary

The existing current-case live path is the bounded supervised pilot. It supports
only the seven complete read-only adapters TC-ACC-08, TC-ROL-04, TC-DI-02, TC-DI-03,
TC-DI-08, TC-HIS-04 and TC-DASH-07 after reviewed cards, current fixture/baseline proof and explicit
start. TC-ACC-10 has only partial E1/E2 source coverage; it is excluded from the
live allowlist because E3 is unresolved and account rows persist. TC-DI-07 has a
complete offline adapter but is excluded due to the uppercase expectation mismatch
and current failure-result handling. The other 22 cases remain unmapped. Existing
component tests provide isolated UI evidence but
do not replace the written black-box procedures or live adapter assertions. An
adapter may be marked source-complete only where every expected item has an exact
assertion method, its prerequisites are explicit, and its mutations/cleanup are
reviewed. Partial historical reports (TC-ACC-10, TC-DI-10, TC-DI-16–19) do not
promote any item to PASS or authorize an unreviewed retest.

For this issue, no browser or product case has run; no Nagios fault,
configuration mutation, merge, acknowledgement, scan, deployment, or service
restart has occurred. A host-only read-only preflight was taken after the user
confirmed the same lab. Any queue produced here remains BLOCKED for live execution
until a supported launcher, reviewed cards, current lab proof, and separate start
exist. Existing successful permission runs are excluded and never replayed.

## Recorded completions and current host observation

- **TC-ACC-09:** complete supervised PASS for E1 and E2, with cleanup and baseline
  restoration, in [the October 18 permissions report](../test-runs/2026-10-18-next-permissions/REPORT.md).
- **TC-SS-04:** complete supervised PASS for E1, with cleanup and baseline
  restoration, in [the October 18 recheck report](../test-runs/2026-10-18-issue-211-ss04-recheck/REPORT.md).

These execution reports do not overwrite the catalog's original Result fields;
the QA workflow keeps new report outcomes separate from those historical entries.
The replacement untested queue must exclude both IDs and retain these report links.

On 2026-10-18 at 10:54 UTC, the read-only `scripts/vmlab preflight --json`
reported the same lab UUID (`351eb491-f5e1-4854-a7e4-68309ad774ad`) running with
host ownership and loopback endpoint checks passing. The supported read-only
`scripts/qa_pilot.py inspect` then passed against the reviewed controlled baseline
and confirmed that the served deployment still matches target
`299ab3ba7203c89a3ca5d8fabea42d9e5f239be2`. It launched no case/browser/transport
and reports no live authorization. A source comparison from that target to the
current repository base (`0f0d563e…`) found changes in DashboardPage,
DeviceInventoryPage and StatusDetailDrawer only for the unacknowledgement
confirmation prompt; that behavior is outside the Module 2–9 adapters.

The current baseline does not establish the required `qa-accounts`/`qa-view`
accounts, device/port fixture for TC-DI-02/03, or no-ping/no-NCPA fixture for
TC-DASH-07. TC-ACC-10 is source-partial only; its E3 branch, persistent account
disposition, and live recovery plan are unresolved. The current run-specific queue
`docs/qa/queues/2026-10-18-modules-2-9-adapters-v1.json` selects only the seven
complete read-only adapters and excludes the other 24 candidates from this run.
It still does not establish the required role/device/dashboard/history fixtures or
complete the live case cards; no case is ready to open. The broader 31-case v10
queue is retained as historical candidate inventory, not the active run scope.

### Latest seven-case queue preparation (2026-10-18)

The active preparation artifact is now
[`2026-10-18-modules-2-9-adapters-v4.json`](queues/2026-10-18-modules-2-9-adapters-v4.json)
with its [Markdown preview](queues/2026-10-18-modules-2-9-adapters-v4.md).
It has two named sets because the supervised runner accepts one set of at most
five cases per invocation: set 01 contains ACC-08, ROL-04, DI-02, DI-03 and
DASH-07; set 02 contains DI-08 and HIS-04. Both set scopes pass
`qa_queue.py check`. The cards bind exact adapter actions, timeout envelope,
source review, current runtime baseline identity, private evidence/control/bridge
outputs and recovery steps.

The fresh read-only inspection at `2026-10-18T12:29:16.826139Z` verified the
controlled deployment target and baseline for the same lab, but case-specific
fixture inputs are absent or unverified. All seven cards therefore remain
BLOCKED. Account/role fixtures are not confirmed, exact device and port labels
are not confirmed, the no-ping/no-NCPA baseline is not confirmed, and the
qualifying real history event is not confirmed. The per-case evidence checklist
is in the [fixture plan](Module_2-9_Fixture_Plan.md). No fixture setup, test
browser, case action, or result has occurred. The former v3 queue/card drafts
are superseded by v8 for preparation; no start record has been created for
either v4 set.
