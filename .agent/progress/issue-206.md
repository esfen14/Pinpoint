# Issue #206: Module-based black-box QA readiness tooling

Branch: `issue-206-qa-readiness`
Status: in-progress

## Finish condition

- [x] Parse/validate 231 TC and 8 E2E cases, requirements, prerequisites and conflicting results.
- [x] Versioned module/person queues with explicit IDs, exclusions, batches, freshness, historical evidence and execution cards.
- [x] Enforce execution-state start/owner/scope/budgets/adapters/evidence/recovery offline; no live QA.
- [x] Inventory/link historical candidates without automatic PASS or invented provenance.
- [x] Migrate legacy validators/rendering/docs links without weakening coverage or rewriting historical outcomes.
- [x] Update reports/workflows/specs and pass isolated checks/docs gate.
- [x] Open reviewable PR with pending human decisions, adapter coverage and separately gated live work.

| Issue requirement | Finish-condition item | Proof |
|---|---|---|
| Catalog/queues | First two items | Parser/queue isolated regression tests and real catalog check |
| Execution constraints | Third item | Offline state/adapter/budget/evidence rejection tests |
| Reuse | Fourth item | Candidate inventory, evidence validation and regression tests |
| Migration | Fifth item | Traceability/render/link validators and docs gate |
| Records and review | Last two items | Report schema, specifications, PR and CI |

## Plan

1. [x] Add shared catalog parser/tests in `scripts/qa_catalog.py`, `scripts/test_qa_catalog.py`.
2. [x] Migrate `scripts/qa_queue.py` and queue tests; add reviewed-evidence validation and historical inventory.
3. [x] Add offline execution-state/card/result validation and tests; do not launch labs or unmapped browser tests.
4. [x] Migrate traceability/rendering/tests/report templates/documentation links and specifications; verify docs.
5. [x] Review finish condition, verify required gates, checkpoint and open PR with explicit remaining live work.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 5 | Self-review added stale accepted-evidence checks (including excluded cases), normative/harness fingerprints, blocked-slot accounting, priority/module context and actual five-batch exhaustion tests | Final `scripts/verify.sh docs`; Python syntax; `git diff --check`; `scripts/verify.sh all` running | Docs green with 66 isolated checks after rejecting unknown prerequisite IDs; full local gate passes: 4310 backend/14 skips, 1003 frontend, build/lint zero errors; no live QA |
| 4 | Migrated source/derived/evidence validators and tests, fixed current/historical links, updated report templates/workflows/specs and docs gate | `scripts/verify.sh docs` | Green: all links and 61 isolated checks pass; no live operations |
| 3 | Added offline session/card/evidence validator with explicit start/owner checks, bounded batches, unchanged adapters, exact action slots and cleanup halt | `python3 -I scripts/test_qa_execute.py` | 7 tests pass; no dispatcher/subprocess exists; live preflight and recovery remain separately gated |
| 2 | Migrated module/person queue v2 and reviewer-bound evidence validation; inventoried 41 reports and attached six partial candidate mappings | `python3 -I scripts/test_qa_queue.py`; `python3 -I scripts/test_qa_evidence.py` | 8 queue and 3 evidence tests pass; no historical PASS inferred; docs migration remains round 4 |
| 1 | Added shared catalog parser with shorthand phase expansion, 239 definitions, complete procedures/expectations and result-conflict handling | `python3 -I scripts/test_qa_catalog.py`; `python3 -I scripts/qa_catalog.py` | 4 tests pass; 231 TC/8 E2E; 26 conflicts plus one free-text verdict flagged; docs gate migration remains step 4 |
| Plan | Copied approved local documentation/catalog transition into isolated issue checkout; recorded implementation plan | `gh issue view 206 --json body --jq .body` | Finish condition covers offline readiness; no live operations authorized |

## State for the next session

- Last check run: `scripts/verify.sh all` (green, `/tmp/issue-206-verify-all.log`), followed by final docs gate (66 checks) and syntax/whitespace validation for QA-only hardening.
- Result: 4310 backend tests passed (14 skips), 1003 frontend passed, build/lint pass with 33 existing warnings and zero errors; final docs checks pass. Draft PR: https://github.com/esfen14/Pinpoint/pull/207. Final-head CI remains to inspect after this checkpoint.
- Next action: Inspect final-head CI on PR #207, then continue current-case adapter/coverage preparation from the overall readiness checklist. Live preflight, atomic scan guarding and pilot runs remain separately gated; no launch authorization is inferred.

## Decisions and notes

- October 15 cutoff remains provisional. Preserve catalog human verdicts; reports retain original executor attribution.
- No product code, lab access, production discovery, installer work or live test execution in this issue.
- Existing related owner changes were copied, not moved; original checkout stays untouched.
- Overall readiness plan remains `.agent/progress/ai-testing-readiness.md`; this file tracks the authorized offline implementation milestone.

- The last hardening check rejects unknown prerequisite references instead of silently ignoring them. Local full-gate product tests ran against unchanged product source; the final QA-only parser change passed the rerun docs gate.
