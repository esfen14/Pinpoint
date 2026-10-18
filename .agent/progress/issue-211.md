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
4. [ ] Prepare fresh immutable recheck card/queue under docs/qa/queues, with explicit pending recovery/start boundaries; obtain separately scoped review/start before any live recovery/attempt. Record observed live result only if authorized.
5. [ ] Re-read issue, verify requirement proofs, checkpoint and open PR against issue-206-qa-readiness; draft if live completion pending. Inspect CI.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Reproduced original rejection before implementation; replaced derived wall end with independent attach bounds/monotonic budget; added real no-browser pinned-worker and real-parser composed regressions; documented timing/trust/uncertainty | scripts/verify.sh docs; scripts/verify.sh frontend; python3 -m py_compile scripts/qa_results.py scripts/qa_pilot.py scripts/qa_container.py; git diff --check | Green: 182 isolated docs contracts, 1003 frontend tests, 8 offline Node checks, build/types/lint (0 errors, 33 existing warnings). Backend skipped per issue; no live access. |
| Plan | Isolated /tmp/pinpoint-issue-211 based on origin/issue-206-qa-readiness at b350f7dc | gh issue view 211; source inspection | Finish conditions covered; no live access |

## State for the next session

- Last check run (exact command): scripts/verify.sh docs > /tmp/issue211-docs.log 2>&1
- Result (first failing lines, or "green"): green; docs and frontend gates pass. Focused parser 13, container 17, composed driver 12 tests pass.
- Hypothesis: Confirmed slot-duration/wall-end category error. Exact attribution of original 44 ms remains unknown without original per-slot telemetry. Independent owned attach bounds remove that inference without a grace period.
- Next action (one specific step, not "continue"): Prepare a new immutable TC-SS-04 recheck queue/card explicitly blocked on reviewed halted-state recovery and new start, then open a draft PR.

## Decisions and notes

- User explicitly chose issue-206-qa-readiness as base; PR targets that branch to keep issue #206 changes separate.
- Existing #206 progress and pilot history are inherited and remain untouched.
- No raw owner reports, credentials or evidence copied; reproduction uses published sanitized timings.
- Issue explicitly requires skipping local backend tests when product backend unchanged; this overrides verify-all backend stage.
- Live recheck requires new review/start and reviewed recovery; task instruction itself is not a queue start. Complete offline fix/preparation first.

- Command-path injection/secret review: only host clock acquisition/receipt forwarding changed; no argv, environment, target, credential or raw-output changes. Same-user malicious record forgery is outside the inherited trusted-driver boundary and documented.
- No browser adapter/config/assertion changes; coverage hashes remain valid, no registry refresh required.
- Final issue re-read returned unchanged finish conditions and no comments.
