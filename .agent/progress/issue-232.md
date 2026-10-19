# Issue #232: Rename System Service label to Network Service

Branch: `issue-232-network-service-label`
Status: ready-for-review

## Finish condition

- [x] Identify the user-visible System Service label reported in QA and change it to Network Service.
- [x] Update matching references in the same flow consistently.
- [x] Preserve service behavior, routes and permissions.

Requirement coverage:

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Identify reported label | Identify and rename | Source search; user clarification needed because no literal label exists |
| Same flow references | Consistent references | Focused rendered UI tests after target confirmed |
| Preserve behavior/routes/permissions | Preserve contracts | Existing route/access/service tests and diff review |
| Separate from #233 | Scope exclusion | No navigation status label changes in this branch |

## Plan

1. [x] Confirm the screen/label with the user; issue explicitly says the screen was not supplied.
2. [x] Read target-owning specification and component, then write a failing label regression.
3. [x] Rename only the confirmed UI label/references and update its specification.
4. [x] Verify focused tests and relevant stage; attempt all gate, remove scaffold and open PR. User requested skipping the CI wait when moving from #233.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Read issue and searched current source | rg -n -i 'system[ _-]+services?' client/src server/app docs/manuals README.md | No literal System Service label. Closest page heading is Service Status Overview at SystemStatusPage.tsx:168. Clarification requested. |

## State for the next session

- Last check run (exact command): rg -n -i 'system[ _-]+services?' client/src server/app docs/manuals README.md
- Result: no matches; no implementation changes made.
- Hypothesis: reported wording may refer to Service Status Overview on /system-status, but the issue does not identify it.
- Next action: remove progress scaffold, open PR with honest checks and leave CI running per user request.

## Decisions and notes

The issue requires identifying the actual reported label before renaming. Asked the user via asynchronous question. Do not guess a different label or alter monitoring/routes/permissions. User requested leaving #233 CI running and proceeding here; PR #264 frontend/docs passed and backend remained running at handoff.

User confirmed: Rename Service Status Overview to Network Service Overview. Target is SystemStatusPage PageHeader title, preserving Overview highlight and all behavior.

Round 1: rendered heading regression failed as expected before title change; 43 focused SystemStatusPage/App/PageAccess tests passed afterward. All 239 coverage records validate. Next: merge current main (#233), then run frontend and all gates.

Round 2: merged current main (#233), preserving Network Status navigation alongside Network Service Overview. Full frontend passed 82 files/1045 tests, build and lint (0 errors, 33 known warnings). All attempted; stops at existing local QA supervisor host-lock failures. Coverage validates all 239 records. No live lab run. User requests no CI wait.
