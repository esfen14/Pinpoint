# Issue #211: Fresh Playwright observation timing

Branch: `issue-211-qa-report-timing`
Status: ready-for-review

## Finish condition

- [x] F1: Reproduce the rejection with sanitized actual timing relationships and pinned report shape.
- [x] F2: Inspect pinned timing/report semantics; document cause and uncertainty.
- [x] F3: Implement a bounded reviewed timing/provenance rule, retaining stale/future/foreign/broadened/retried/forged/incomplete rejection and all assertions.
- [x] F4: Add import/driver regressions (44 ms, foreign/stale, failed cleanup); run focused helpers/docs; skip unchanged application backend tests.
- [x] F5: Preserve original INCONCLUSIVE report, evidence, consumed v4 slot and halted ledger; no recovery/replay without separate review/start.
- [x] F6: Prepare new reviewed recheck card; prove supervised result/cleanup on separately explicitly started run, retaining original outcome.

Requirement coverage:

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Sanitized actual relationship, pinned shape | F1 | scripts/test_qa_results.py fixture/regression |
| Duration versus wall clock semantics and uncertainty | F2 | pinned source inspection and timing investigation note |
| Bounded provenance, no arbitrary tolerance or weaker assertions | F3 | parser and adversarial focused regressions |
| Import/driver/cleanup regressions, focused helpers/docs | F4 | unittest helpers, offline Node checks, scripts/verify.sh docs |
| Preserve history/private evidence/halted ledger; no replay | F5 | unchanged historical files; no live commands or ledger mutation |
| Fresh card and explicitly started complete live path | F6 | new queue preview/check; later authorized supervised run report |
| Harness defect, no product permission finding | F2, F5 | investigation note and unchanged product code |

## Plan

1. [x] Inspect pinned reporter/worker source and reproduce 44 ms rejection in scripts/test_qa_results.py; document semantics in docs/qa/QA_Report_Timing.md.
2. [x] Implement bounded provenance rule in scripts/qa_results.py and, only if necessary, adapter/config/driver sources; add meaningful import/driver regressions in scripts/test_qa_results.py and scripts/test_qa_pilot.py; review source hashes when affected.
3. [x] Update owning spec files/Agent_Workflow_and_CI.md, spec files/Implementation_Status.md and docs/qa/Automation_Readiness.md; verify focused Python/Node helpers and docs gate, with backend omitted per issue.
4. [x] Prepare source-reviewed immutable recheck card/queue under docs/qa/queues and docs/qa/Issue_211_Recheck_Review.md, blocked on recovery/start; check freshness and refusal to execute.
5. [x] Implement approved audited recovery in scripts/qa_supervisor.py and scripts/qa_recovery.py with isolated tests, preserving original attempt/session data and an exact private ledger archive; gate it on an expiring queue/attempt/checksum-bound recovery grant and fresh cleanup/baseline proof. Wire an explicit recover CLI in scripts/qa_pilot.py, update specs/docs, verify focused helpers/docs.
6. [x] Prepare/check/show the source-current v2 replacement card after recovery source changes; validate the source card and missing-start rejection; create only new empty private v2 output directories.
7. [x] Paeng separately authorized recovery use and conditionally explicitly started v2; actual audited recovery and one supervised browser attempt succeeded, accepted PASS/restored. New report/index/execution log recorded; original outcome/archive/attempt/budgets preserved.
8. [x] Re-read unchanged issue, prove all finish items and run final docs gate; PR #212 opened against issue-206-qa-readiness and CI inspected. Final outcome/body/progress removal and latest-head CI are finish steps below, not another implementation round.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| Plan | Isolated /tmp/pinpoint-issue-211 based on origin/issue-206-qa-readiness at b350f7dc | gh issue view 211; source inspection | Finish conditions covered; no live access |
| 1 | Reproduced original rejection before implementation; replaced derived wall end with independent attach bounds/monotonic budget; added real no-browser pinned-worker and real-parser composed regressions; documented timing/trust/uncertainty | scripts/verify.sh docs; scripts/verify.sh frontend; python3 -m py_compile scripts/qa_results.py scripts/qa_pilot.py scripts/qa_container.py; git diff --check | Green: 182 isolated docs contracts, 1003 frontend tests, 8 offline Node checks, build/types/lint (0 errors, 33 existing warnings). Backend skipped per issue; no live access. |
| 2 | Prepared fresh #211 one-case recheck v1 and concrete recovery review; card deliberately non-executable, original pilot/v4/product sources unchanged | qa_queue.py prepare/check/show; validate_card negative check; git diff --quiet for original pilot/v4/application; scripts/verify.sh docs | Green: fresh scope, missing review fails closed, 182 isolated docs contracts. No live resource or private ledger/evidence accessed. |

| 3 | Implemented user-approved audited recovery core/collector/CLI with exact private original-state archive, preserved halted attempts/budgets, expiring scope/evidence-bound grant, fresh absence/baseline proof and new-queue-only consumption | python3 -I scripts/test_qa_recovery.py; scripts/verify.sh docs > /tmp/issue211-recovery-docs-serial.log 2>&1; Python compile; git diff --check | Green: 11 new recovery contracts, full 193 isolated docs contracts. An earlier docs run collided with my concurrently run helper on the canonical test lock; serial rerun passed without weakening locks/tests. No live commands or real ledger/evidence access. |

| 4 | Prepared immutable v2 exact TC-SS-04 executable-intent scope with recovery/launcher vectors and disjoint empty private outputs; v1 remains historical/stale. Updated recovery review sequence to freeze queue before its grant-bound disposition | qa_queue.py prepare/check/show; validate_card; grant_check negative; scripts/verify.sh docs > /tmp/issue211-v2-docs.log 2>&1; check_doc_links.py; git diff --check | Green: source-current scope 1a63336e7ceca199685233a85c3038bc075e6ab45ff800a51d73ffbed9c05d00; 193 docs contracts; 218 linked documents. No actual recovery, existing evidence access or browser start. |

| 5 | Applied separately authorized exact recovery (08:25:45 UTC), then separately started one v2 TC-SS-04 initial browser attempt; actual PASS accepted 08:26:57 UTC after strict fresh import/logout/resource cleanup/post-baseline proof. Recorded report/index/queue log and owning status without altering original pilot | Exact card recovery_argv/launcher_argv; post-run ledger/archive/budget audit; scripts/verify.sh docs > /tmp/issue211-live-report-docs.log 2>&1; unchanged-original diff; git diff --check | Green: 193 docs contracts. New E1 is 47 ms beyond old invalid derived end, accepted by independent actual attach bounds; result PASS/restored, old attempt still halted/INCONCLUSIVE, original budgets unchanged. One new batch/case completed, zero retry/E2E; code unchanged during execution. |

## State for the next session

- Last check run (exact command): scripts/verify.sh docs > /tmp/issue211-live-report-docs.log 2>&1
- Result (first failing lines, or "green"): green; 193 docs contracts pass, including 11 recovery, 13 parser, 17 container and 12 composed driver tests. Earlier frontend gate passed 1003 product and 8 helper tests; no frontend changed during recovery implementation.
- Hypothesis: Confirmed slot-duration/wall-end category error. Exact attribution of original 44 ms remains unknown without original per-slot telemetry. Independent owned attach bounds remove that inference without a grace period.
- Next action (one specific step, not "continue"): Finish delivery: remove only issue-211 progress scaffolding, push outcome, update PR #212, verify latest-head CI. Retain inherited issue-206 progress; keep stacked PR draft because ready-PR CI rejects any inherited issue progress file.

## Decisions and notes

- User explicitly chose issue-206-qa-readiness as base; PR targets that branch to keep issue #206 changes separate.
- Existing #206 progress and pilot history are inherited and remain untouched.
- No raw owner reports, credentials or evidence copied; reproduction uses published sanitized timings.
- Issue explicitly requires skipping local backend tests when product backend unchanged; this overrides verify-all backend stage.
- Live recheck requires new review/start and reviewed recovery; task instruction itself is not a queue start. Complete offline fix/preparation first.

- Command-path injection/secret review: only host clock acquisition/receipt forwarding changed; no argv, environment, target, credential or raw-output changes. Same-user malicious record forgery is outside the inherited trusted-driver boundary and documented.
- No browser adapter/config/assertion changes; coverage hashes remain valid, no registry refresh required.
- Final issue re-read returned unchanged finish conditions and no comments.

- Previous blocking question answered: Paeng approved recovery implementation; it is complete. Current blocker: applying actual recovery and starting the named v2 case still need separate explicit authorization. No such use/start is inferred from implementation approval.
- Prepared queue: docs/qa/queues/2026-10-18-issue-211-ss04-recheck-v1.json; set issue211-ss04-recheck; owner Paeng; target 299ab3ba7203c89a3ca5d8fabea42d9e5f239be2; scope checked source-current.

- User explicitly approved recovery implementation via the PR #212 recovery-scope question. Plan expanded on that authorization; approval is for implementation, not applying live recovery or starting a browser. PR: https://github.com/esfen14/Pinpoint/pull/212 (draft, base issue-206-qa-readiness).

- Recovery core/CLI implemented and verified under the approved scope. Approval does not yet authorize applying it to the real store or a browser run. The historical v1 card remains unexecuted and now correctly stale after recovery source/spec changes.

- Current queue: docs/qa/queues/2026-10-18-issue-211-ss04-recheck-v2.json; set/next session issue211-ss04-recheck-v2; owner Paeng; application target unchanged. Card human_required=false records no human E1 requirement, not runtime proof or consent. Original ledger is still untouched/halted.

- Paeng explicitly authorized actual recovery use and separately started exactly v2 set/session issue211-ss04-recheck-v2, conditional on successful recovery/fresh preflight. Private recovery grant and authorization summary are bound to actual original one-attempt halted ledger, original evidence hash, v2 scope, unchanged target/UUID/baseline and 15-minute expiry. No browser start grant exists yet.

- Actual report: docs/test-runs/2026-10-18-issue-211-ss04-recheck/REPORT.md. Harness tested 724a4b55dd6983809fc2b91afb876441c4a275d8, app unchanged 299ab3ba7203c89a3ca5d8fabea42d9e5f239be2. Original exact private ledger archive and original budget entries independently audited after the new accepted result.
- v2 immutable JSON remains unchanged and consumed; expected source-stale status after the owning known-gap inventory update was verified. No replay or new start is authorized. Source journal label remains active with no active case/batch, accepted result and completion event; durable supervised attempt is complete.
- The only delivery constraint is inherited .agent/progress/issue-206.md on the base. check_agent_progress.py --none rejects any such file on ready PRs; do not delete another unfinished issue's state or weaken the gate. Keep #212 draft while its parent carries that scaffolding; #211 finish conditions themselves are all proven.
