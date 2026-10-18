# #211 recheck review — prepared, not started

The [v1 recheck preview](queues/2026-10-18-issue-211-ss04-recheck-v1.md) and
[immutable JSON](queues/2026-10-18-issue-211-ss04-recheck-v1.json) select only
TC-SS-04, one initial attempt, one worker, zero retries, owned by Paeng under
tracking issue #211. Target remains `299ab3ba7203c89a3ca5d8fabea42d9e5f239be2`.
This is an explicit diagnostic recheck after the
[INCONCLUSIVE pilot](../test-runs/2026-10-18-issue-206-ss04-pilot/REPORT.md),
not a new untested slot or accepted retest of a merged product fix.

Source review covers the unchanged Staff/UI/redirect/logout assertions and the
[bounded timing fix](QA_Report_Timing.md). No account, product, browser assertion,
case expectation, scope or verdict rule was changed to obtain a pass. The source
coverage register remains current. Queue `check` passes; that is neither live
readiness nor exclusive lab ownership.

## Required recovery review

The original UUID ledger is halted. The supported supervisor deliberately rejects
all dispatch while any attempt remains unresolved; a new queue cannot bypass it.
The explicit `qa_pilot.py recover` command implements the approved recovery
mechanism below. It has not been applied to the real ledger. Do not clear, replace,
delete, relocate or manually rewrite the store, reclassify the original result or reuse v4.

Before an executable replacement card/start, separately review a recovery scope:

1. Acquire the existing cooperative host/UUID claim, preserving original private
   evidence and the consumed v4 attempt/session exactly as recorded.
2. Inspect the owned container/bridge/process cleanup and browser logout evidence,
   and obtain fresh supported read-only inspection against the controlled baseline.
   These are prerequisites for recovery, not retrospective PASS evidence.
3. If recovery is approved, define an auditable recovery mechanism that retains
   the original halted attempt and records the reviewer, evidence and disposition.
   Implementation was separately approved by Paeng. The implementation archives
   exact original ledger bytes privately, leaves every attempt and budget unchanged,
   appends an evidence/grant-bound recovery disposition, and updates only the active
   halt gate. Every readiness check verifies the archive/history; only the exact
   named new queue may consume another slot. This supplies no reset or alternate store.
4. Obtain fresh exclusive ownership, exact host/guest/boot/runtime/source/Staff/
   served-byte/image/browser observations. A reboot or baseline change blocks;
   preparing this card does not authorize redeployment/restart/reset/account work.
5. Prepare a new immutable executable replacement card reflecting actual recovery
   and baseline observations; validate its sources and obtain a separate explicit
   start bound to that queue/set/owner/new session/UUID/target/expiry.

The v1 card keeps `human_required: true` to enforce this missing review gate.
Its baseline/image values are pins from the previous report, not fabricated fresh
attestations. Proposed output paths are disjoint from v4; none was created during
preparation. The listed launcher vector is not permission to execute it.

## Pending live result

After the separately authorized start, require the complete supported supervisor
path: durable new-attempt consumption, actual one-case browser execution, strict
current-run import, logout/401 evidence, owned container removal/daemon absence,
bridge/process cleanup and fresh independent baseline proof. Save a new attributable
report, index and execution log; keep original results and TC/E2E counts separate.
Stop on uncertainty, with no repeat or automatic recovery. Until this run is
observed, #211 finish condition 6 and broad/unattended readiness remain incomplete.

## Approved mechanism and remaining authorization

The separate `supervised recovery` grant requires `explicit_recovery: true`, reviewer,
UUID, exact current ledger checksum, last halted-attempt hash, reviewed original
evidence hash, next queue hash, unchanged target/baseline hashes and expiry. It
is checked under the existing host/UUID locks before external probes/output work,
then rechecked before disposition. It is distinct from a `supervised live` start.

`qa_recovery.py` validates the prior immutable queue, original terminal container/
bridge metadata, halted session and exact browser logout attachment without importing
its case result. It requires successful fresh empty Docker queries for both original
ID and name, absence of original same-user transport processes/Unix endpoints,
unchanged evidence and fresh supported baseline inspection. Queries and observations
are bounded; total returned proof must fit 90 seconds. No browser, kill/remove,
restart/reset, account operation or accepted historical verdict is performed.

The original ledger is copied byte-for-byte into a private write-once checksum-named
archive before the current state is atomically saved. A failed/changed archive,
interrupted checkpoint, running attempt, missing/expired grant, failed proof or
subsequent halt remains blocked. Original attempts retain `status=halted`; audit
records include proof/review/evidence digests, target, baseline, next queue and time.
Old slots remain consumed and old budgets remain counted.

Implementation authorization has been received. Applying this mechanism on the
actual appliance/store has **not** been authorized or executed. A separate explicit
start is still required for a browser run. The v1 card remains historical preparation
and becomes source-stale after recovery source changes; prepare a replacement.

A recovery grant must bind the exact executable-intent replacement queue. Changing
that queue after recovery will be rejected. Its source-reviewed adapter needs no
human product observation (`human_required: false`); that field does not attest
live prerequisites or authorize launch. Actual recovery, exclusive ownership,
baseline and separate explicit start are enforced by the supported runtime gates.
The v1 use of `human_required: true` was a preparation block and cannot be the
queue authorized for dispatch by a recovery record.
