# Issue #233: Rename System Status to Network Status

Branch: `issue-233-network-status-label`
Status: in-progress

## Finish condition

- [x] Sidebar and matching shell header/history references say Network Status.
- [x] Existing route, permissions and monitoring behavior preserved.
- [x] Device Inventory → Network Status → Topology order preserved.
- [x] Applicable UI specifications use approved terminology.

Requirement coverage:

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Rename visible page identity | Sidebar and header | PageAccess and LayoutSettings tests, source search |
| Preserve route and permissions | Existing route and permissions | App and PageAccess tests, diff inspection |
| Preserve monitoring | Monitoring behavior | SystemStatusPage tests; no monitoring code change |
| Preserve #231 order | Consecutive sidebar entries | PageAccess sidebar order assertion |
| Update specifications | Approved terminology | Frontend_Modules_and_Routes, Implementation_Status, AGENTS router references; docs checks |
| Separate #232 | Scope exclusion | No System Service wording change |

## Plan

1. [x] Update PageAccess and LayoutSettings tests for sidebar/header/history wording; confirm failures.
2. [x] Update Sidebar.tsx and Header.tsx visible labels, applicable UI references in specifications and AGENTS.md; preserve internal names and Settings configuration summary.
3. [x] Run focused tests, frontend/docs gates and all verification; inspect coverage freshness and final issue requirements.
4. [ ] Remove progress file, open PR and wait for green CI.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Read issue, requirements and source; created plan | git status --short | clean before plan |
| 1 | Added tests first; changed shell labels and matching docs; reviewed QA adapter/fingerprints | focused Vitest PageAccess/LayoutSettings/App/SystemStatusPage | 3 expected failures before change; 49 passed after |
| 2 | Full frontend and all gate; reread unchanged issue | TMPDIR=/private/tmp scripts/verify.sh frontend; TMPDIR=/private/tmp scripts/verify.sh all | frontend green: 1044 tests, build, zero lint errors/33 known warnings. All stops at existing macOS QA supervisor host-lock failures; supported Linux CI required |

## State for the next session

- Last check run (exact command): TMPDIR=/private/tmp npm exec --prefix client -- vitest run src/test/PageAccess.test.tsx src/test/LayoutSettings.test.tsx src/test/App.test.tsx src/test/SystemStatusPage.test.tsx --root client
- Result: frontend green; all gate stops in QA supervisor with Host controller unavailable, already owned or unsafe (known local /tmp compatibility).
- Hypothesis: two shell label constants implement this rename; Settings System Status is a separate configuration summary, not this page.
- Next action: remove scaffold, open PR with local limitation and wait for Linux CI.

## Decisions and notes

Use the work-issue workflow. No live lab required or authorized for this naming-only issue. Keep /system-status, SystemStatusPage and system.network_health identifiers. The page content heading is Service Status Overview, not System Status, and is unchanged. Historical reports and case IDs remain historical records.
