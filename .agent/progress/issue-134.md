# Issue #134: Reconcile Reports documentation

Branch: `issue-134-reports-documentation`
Status: in-progress

## Finish condition

- [ ] E / Part 21.1: both inventories accurately list all six views.
- [ ] E / Part 21.1: each view names its API route.
- [ ] E / Part 21.1: `scripts/verify.sh docs` passes.
- [ ] C / Part 21.1: record displayed fields, period handling and export support; file defects separately.
- [ ] F/G/H applicable evidence: full verification and sanitized report, including six-view appliance checks.

Requirement coverage:

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| C/E Part 21.1 six views, endpoints, periods, exports | First four items | Source audit in frontend spec and docs verification |
| Parts 21.2/21.3 targets, validation, migration, indicators, exports | Deliberately out of scope | User rejected targets on 2026-10-17: measured uptime only |
| F source/API/model/components/tests/help changes | Inapplicable without behavior changes | Documentation-only diff; existing regression suite |
| F technical docs | Owning frontend and implementation inventories | Source audit; other specs updated only if inaccurate |
| F/G evidence and six-view appliance check | Last item | Sanitized report and verify output |
| H functional, quality, tests, security, docs, PR gates | Applicable documentation, verification and PR requirements | verify all, diff review, PR and CI; reviewer approval remains human |
| Recurring emailed reports | Explicitly out of scope | Issue condition and unchanged application |

## Plan

1. [ ] Audit ReportsPage.tsx, components/reports, report types/exports and server/app/api/system/report.py; update spec files/Frontend_Modules_and_Routes.md, Implementation_Status.md and docs/issues/issue-021.md to record the product decision.
2. [ ] Run docs and all verification, inspect six report views on a lab appliance if available, and record docs/test-runs evidence; report any defects separately.
3. [ ] Re-read #134, prove applicable finish conditions, remove progress file when complete and open PR using the template; inspect CI.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| Intake | Scope narrowed by explicit user decision | gh issue view 134 --json number,title,body,comments,state | Part 21.1 remains; targets rejected |

## State for the next session

- Last check run (exact command): git worktree add -b issue-134-reports-documentation /tmp/pinpoint-issue-134 origin/main
- Result (first failing lines, or "green"): green
- Hypothesis: six views already exist; inventories are stale. No application behavior change is needed.
- Next action (one specific step, not "continue"): Complete the six-view source audit and update the frontend inventory.

## Decisions and notes

The user explicitly decided: "pinpoint does not need the feature, we only need to show the measured uptime, which I think it already does". This supersedes conditional Parts 21.2/21.3 and their deliverables. No new dependency, migration, permission or setting is required. No new tests for prose-only changes. Manual lab requirements will be recorded honestly if unavailable.
