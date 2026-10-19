# Issue #233: Rename System Status to Network Status

Branch: `issue-233-network-status-label`
Status: in-progress

## Finish condition

- [ ] Sidebar and matching shell header/history references say Network Status.
- [ ] Existing route, permissions and monitoring behavior preserved.
- [ ] Device Inventory → Network Status → Topology order preserved.
- [ ] Applicable UI specifications use approved terminology.

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

1. [ ] Update PageAccess and LayoutSettings tests for sidebar/header/history wording; confirm failures.
2. [ ] Update Sidebar.tsx and Header.tsx visible labels, applicable UI references in specifications and AGENTS.md; preserve internal names and Settings configuration summary.
3. [ ] Run focused tests, frontend/docs gates and all verification; inspect coverage freshness and final issue requirements.
4. [ ] Remove progress file, open PR and wait for green CI.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Read issue, requirements and source; created plan | git status --short | clean before plan |

## State for the next session

- Last check run (exact command): git status --short
- Result: clean before plan creation.
- Hypothesis: two shell label constants implement this rename; Settings System Status is a separate configuration summary, not this page.
- Next action: update existing sidebar/header tests and confirm they fail for the old label.

## Decisions and notes

Use the work-issue workflow. No live lab required or authorized for this naming-only issue. Keep /system-status, SystemStatusPage and system.network_health identifiers. The page content heading is Service Status Overview, not System Status, and is unchanged. Historical reports and case IDs remain historical records.
