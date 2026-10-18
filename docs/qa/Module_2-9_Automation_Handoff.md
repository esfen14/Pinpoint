# Modules 2–9 automation and manual test handoff

Issue: [#214](https://github.com/esfen14/Pinpoint/issues/214)

This handoff separates source automation from actual execution. No Module 2–9
case in this queue has been run by the new adapter suite. The current executable
scope is [queue v11](queues/2026-10-18-modules-2-9-adapters-v12.json); its
seven adapters are ready at source level but blocked on case fixtures and a
separate start for each named set.

## Work completed

- Added source-reviewed Playwright adapters and explicit case selection for
  TC-ACC-08, TC-ROL-04, TC-DI-02, TC-DI-03, TC-DI-08, TC-HIS-04 and TC-DASH-07.
- Added a module-specific Playwright config, selection helper, QA TypeScript
  config, coverage mappings, exact expected-item markers and read-only guards
  for the device service dialogs.
- Extended the supervised pilot and result handling for these seven cases;
  generated source-bound execution cards, private evidence/output paths, and a
  seven-case queue split into two supported sets.
- Documented prerequisites, recovery boundaries, the fixture creation limits,
  and the 24 deferred candidates in the adapter review and fixture plan.
- Verified offline selection/collection, source coverage, result/transport/pilot
  contracts, QA TypeScript, frontend verification and docs verification. These
  are harness checks only.

## Cases with complete source adapters

These seven cases can be automated by the current supervised runner once their
exact fixture facts are verified. The cases are read-only; the adapters do not
create roles, accounts, devices, ports, or history.

| Case | Automated coverage | Still needed before execution |
|---|---|---|
| TC-ACC-08 | Super Admin alert checkbox/column and restricted-user checkbox visibility | Existing `qa-accounts` role and assigned user with the exact permission set; private credentials. |
| TC-ROL-04 | Dashboard-only sidebar, 13 protected page redirects, and three API 403s | Existing `qa-view` user with only `system.dashboard` and private credentials. |
| TC-DI-02 | Port group order, counts/nonempty groups, and TCP/UDP ordering | Exact existing device with Monitored, Suggested, Stopped and Archived ports. |
| TC-DI-03 | Held mismatched Suggested port and its single explanation | Exact existing port showing Held, Not used as intended, expected/found services and unacknowledged state. |
| TC-DI-08 | TCP known/generic service choices, UDP unsupported service, warning text | Exact editable TCP and UDP ports on the reviewed device; TCP options include `http`. Adapter blocks port writes and cancels dialogs. |
| TC-HIS-04 | Valid/invalid alert-history date-range API behavior | Super Admin history permission and a real alert event older than 25 hours within the rolling 30 days. Do not seed timestamps or change the clock. |
| TC-DASH-07 | Dashboard no-data cards | Appliance already has no ping check and no NCPA host/data. Do not remove monitoring to create this condition. |

Queue v11 places the first five in `modules-2-9-adapters-01` and the last two
in `modules-2-9-adapters-02`. They require separate explicit starts. The
controlled runtime baseline passed a read-only inspection on October 18, 2026;
that did not verify case fixtures. Every card currently records
`case_fixtures: UNVERIFIED`, so none is live-ready yet.

## Cases to handle manually or defer

The original candidate inventory contains 31 cases. After selecting the seven
above, 24 remain outside this automation run:

- **TC-ACC-10:** only E1/E2 have partial automation. E3 requires an unusual
  no-active-roles state; created account rows and audit entries persist. Use
  manual testing only on a disposable appliance with a reviewed recovery plan.
- **TC-DI-07:** an offline adapter exists, but the observed source behavior
  lowercases input while the case expects uppercase rejection. Manually inspect
  without saving and record the discrepancy; do not call it a pass until the
  expected behavior and result handling are resolved.
- **22 cases without complete adapters:**
  TC-NH-05, TC-NH-06, TC-NH-07, TC-DI-05, TC-DI-06, TC-DI-09, TC-DI-11,
  TC-DI-12, TC-DI-13, TC-DI-14, TC-DI-15, TC-DI-16, TC-DI-17, TC-DI-18,
  TC-DI-19, TC-ACK-04, TC-ACK-07, TC-ACK-08, TC-DI-10, TC-DASH-09,
  TC-SS-05 and TC-DASH-06. Follow the catalog procedures manually when the
  fixture is available. Cases that stop/resume services, change monitoring,
  acknowledge alerts, merge devices, fault services, or restart Nagios need
  their own isolation and recovery review first. TC-DI-19 is irreversible
  without a disposable target.

“Manual candidate” does not mean immediately runnable. Apply the catalog
prerequisites and the [fixture plan](Module_2-9_Fixture_Plan.md) to each case;
missing prerequisites remain blocked. TC-ACC-09 and TC-SS-04 are not in the
24-case remainder: accepted supervised PASS reports already exist for them.

## Run status and next steps

No case in this seven-case queue has a result. The current status is:

1. Merge the adapter and handoff PR when reviewed.
2. Manually exercise the 24 deferred candidates whose prerequisites and
   recovery plan are satisfied; preserve exact observations and evidence.
3. For automated cases, use an appliance with the required existing fixtures or
   a separately reviewed isolated setup. Do not manufacture the no-ping/NCPA
   condition or aged history event in the shared lab.
4. Refresh the queue/cards and current preflight after fixture facts are known.
   Start each named set separately under `.agent/workflows/qa-run.md`.
5. Record any execution in a new attributable report under `docs/test-runs/`;
   do not edit the catalog’s historical result cells.

The [adapter review](Module_2-9_Adapter_Review.md),
[fixture plan](Module_2-9_Fixture_Plan.md), and
[automation readiness guide](Automation_Readiness.md) hold the detailed source,
coverage, scope and safety notes.
