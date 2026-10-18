# Issue #206: Module-based black-box QA readiness tooling

Branch: `issue-206-qa-readiness`
Status: in-progress

## Finish condition

- [ ] Parse/validate 231 TC and 8 E2E cases, requirements, prerequisites and conflicting results.
- [ ] Versioned module/person queues with explicit IDs, exclusions, batches, freshness, historical evidence and execution cards.
- [ ] Enforce execution-state start/owner/scope/budgets/adapters/evidence/recovery offline; no live QA.
- [ ] Inventory/link historical candidates without automatic PASS or invented provenance.
- [ ] Migrate legacy validators/rendering/docs links without weakening coverage or rewriting historical outcomes.
- [ ] Update reports/workflows/specs and pass isolated checks/docs gate.
- [ ] Open reviewable PR with pending human decisions, adapter coverage and separately gated live work.

| Issue requirement | Finish-condition item | Proof |
|---|---|---|
| Catalog/queues | First two items | Parser/queue isolated regression tests and real catalog check |
| Execution constraints | Third item | Offline state/adapter/budget/evidence rejection tests |
| Reuse | Fourth item | Candidate inventory, evidence validation and regression tests |
| Migration | Fifth item | Traceability/render/link validators and docs gate |
| Records and review | Last two items | Report schema, specifications, PR and CI |

## Plan

1. [ ] Add shared catalog parser/tests in `scripts/qa_catalog.py`, `scripts/test_qa_catalog.py`.
2. [ ] Migrate `scripts/qa_queue.py` and queue tests; add reviewed-evidence validation and historical inventory.
3. [ ] Add offline execution-state/card/result validation and tests; do not launch labs or unmapped browser tests.
4. [ ] Migrate traceability/rendering/tests/report templates/documentation links and specifications; verify docs.
5. [ ] Review finish condition, verify required gates, checkpoint and open PR with explicit remaining live work.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| Plan | Copied approved local documentation/catalog transition into isolated issue checkout; recorded implementation plan | `gh issue view 206 --json body --jq .body` | Finish condition covers offline readiness; no live operations authorized |

## State for the next session

- Last check run: `gh issue view 206 --json body --jq .body`
- Result: Issue scope and finish condition recorded.
- Next action: Write parser regression tests, observe failure, implement shared parser.

## Decisions and notes

- October 15 cutoff remains provisional. Preserve catalog human verdicts; reports retain original executor attribution.
- No product code, lab access, production discovery, installer work or live test execution in this issue.
- Existing related owner changes were copied, not moved; original checkout stays untouched.
- Overall readiness plan remains `.agent/progress/ai-testing-readiness.md`; this file tracks the authorized offline implementation milestone.
