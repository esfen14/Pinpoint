# Issue #211: Fresh Playwright observation timing

Branch: `issue-211-qa-report-timing`
Status: in-progress

## Finish condition

- [x] F1: Reproduce the rejection with sanitized actual timing relationships and pinned report shape.
- [x] F2: Inspect pinned timing/report semantics; document cause and uncertainty.
- [x] F3: Implement a bounded reviewed timing/provenance rule, retaining stale/future/foreign/broadened/retried/forged/incomplete rejection and all assertions.
- [x] F4: Add import/driver regressions (44 ms, foreign/stale, failed cleanup); run focused helpers/docs; skip unchanged application backend tests.
- [x] F5: Preserve original INCONCLUSIVE report, evidence, consumed v4 slot and halted ledger; no recovery/replay without separate review/start.
- [ ] F6: Prepare new reviewed recheck card; prove supervised result/cleanup on separately explicitly started run, retaining original outcome.

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
6. [ ] Prepare a replacement recheck card after recovery source changes; obtain authorization before applying live recovery and a separate explicit new start before a browser run. Record a new supervised result only if authorized.
7. [ ] Re-read issue, verify requirement proofs, checkpoint and open PR against issue-206-qa-readiness; draft if live completion pending. Inspect CI.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| Plan | Isolated /tmp/pinpoint-issue-211 based on origin/issue-206-qa-readiness at b350f7dc | gh issue view 211; source inspection | Finish conditions covered; no live access |
| 1 | Reproduced original rejection before implementation; replaced derived wall end with independent attach bounds/monotonic budget; added real no-browser pinned-worker and real-parser composed regressions; documented timing/trust/uncertainty | scripts/verify.sh docs; scripts/verify.sh frontend; python3 -m py_compile scripts/qa_results.py scripts/qa_pilot.py scripts/qa_container.py; git diff --check | Green: 182 isolated docs contracts, 1003 frontend tests, 8 offline Node checks, build/types/lint (0 errors, 33 existing warnings). Backend skipped per issue; no live access. |
| 2 | Prepared fresh #211 one-case recheck v1 and concrete recovery review; card deliberately non-executable, original pilot/v4/product sources unchanged | qa_queue.py prepare/check/show; validate_card negative check; git diff --quiet for original pilot/v4/application; scripts/verify.sh docs | Green: fresh scope, missing review fails closed, 182 isolated docs contracts. No live resource or private ledger/evidence accessed. |

| 3 | Implemented user-approved audited recovery core/collector/CLI with exact private original-state archive, preserved halted attempts/budgets, expiring scope/evidence-bound grant, fresh absence/baseline proof and new-queue-only consumption | python3 -I scripts/test_qa_recovery.py; scripts/verify.sh docs > /tmp/issue211-recovery-docs-serial.log 2>&1; Python compile; git diff --check | Green: 11 new recovery contracts, full 193 isolated docs contracts. An earlier docs run collided with my concurrently run helper on the canonical test lock; serial rerun passed without weakening locks/tests. No live commands or real ledger/evidence access. |

## State for the next session

- Last check run (exact command): scripts/verify.sh docs > /tmp/issue211-recovery-docs-serial.log 2>&1
- Result (first failing lines, or "green"): green; 193 docs contracts pass, including 11 recovery, 13 parser, 17 container and 12 composed driver tests. Earlier frontend gate passed 1003 product and 8 helper tests; no frontend changed during recovery implementation.
- Hypothesis: Confirmed slot-duration/wall-end category error. Exact attribution of original 44 ms remains unknown without original per-slot telemetry. Independent owned attach bounds remove that inference without a grace period.
- Next action (one specific step, not "continue"): Prepare a source-current v2 replacement queue/card for exactly TC-SS-04, keeping runtime recovery/use and explicit browser start pending; update draft PR #212 with verified recovery implementation.

## Decisions and notes

- User explicitly chose issue-206-qa-readiness as base; PR targets that branch to keep issue #206 changes separate.
- Existing #206 progress and pilot history are inherited and remain untouched.
- No raw owner reports, credentials or evidence copied; reproduction uses published sanitized timings.
- Issue explicitly requires skipping local backend tests when product backend unchanged; this overrides verify-all backend stage.
- Live recheck requires new review/start and reviewed recovery; task instruction itself is not a queue start. Complete offline fix/preparation first.

- Command-path injection/secret review: only host clock acquisition/receipt forwarding changed; no argv, environment, target, credential or raw-output changes. Same-user malicious record forgery is outside the inherited trusted-driver boundary and documented.
- No browser adapter/config/assertion changes; coverage hashes remain valid, no registry refresh required.
- Final issue re-read returned unchanged finish conditions and no comments.

- Blocking question: Approve a separate audited halted-state recovery scope described in docs/qa/Issue_211_Recheck_Review.md before implementation/use; no supported recovery command currently exists. A later executable replacement card and explicit start are still required. The source-reviewed v1 card retains human_required=true and is not a live start.
- Prepared queue: docs/qa/queues/2026-10-18-issue-211-ss04-recheck-v1.json; set issue211-ss04-recheck; owner Paeng; target 299ab3ba7203c89a3ca5d8fabea42d9e5f239be2; scope checked source-current.

- User explicitly approved recovery implementation via the PR #212 recovery-scope question. Plan expanded on that authorization; approval is for implementation, not applying live recovery or starting a browser. PR: https://github.com/esfen14/Pinpoint/pull/212 (draft, base issue-206-qa-readiness).

- Recovery core/CLI implemented and verified under the approved scope. Approval does not yet authorize applying it to the real store or a browser run. The historical v1 card remains unexecuted and now correctly stale after recovery source/spec changes.
