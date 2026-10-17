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

1. [x] Audit ReportsPage.tsx, components/reports, report types/exports and server/app/api/system/report.py; update spec files/Frontend_Modules_and_Routes.md, Implementation_Status.md and docs/issues/issue-021.md to record the product decision.
2. [ ] Run docs and all verification, inspect six report views on a lab appliance if available, and record docs/test-runs evidence; report any defects separately.
3. [x] On user steering, write docs/plans/Service_Reports_Nagios_Availability_Plan.md for the two service reports; do not implement or open the documentation PR until follow-up scope is settled.
4. [ ] Re-read #134, prove applicable finish conditions, remove progress file when complete and open PR using the template; inspect CI.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| Planning | Drafted the user-requested Nagios-backed service-report plan | scripts/verify.sh docs | green; no product implementation |
| 1 | Source audit and documentation reconciliation; recorded rejection of targets | scripts/verify.sh docs | green |
| Intake | Scope narrowed by explicit user decision | gh issue view 134 --json number,title,body,comments,state | Part 21.1 remains; targets rejected |

## State for the next session

- Last check run (exact command): scripts/verify.sh docs
- Result (first failing lines, or "green"): green
- Hypothesis: six views already exist; inventories are stale. No application behavior change is needed.
- Next action (one specific step, not "continue"): Present the saved service-report plan; establish an implementation issue with its acceptance criteria before changing application behavior.

## Decisions and notes

The user explicitly decided: "pinpoint does not need the feature, we only need to show the measured uptime, which I think it already does". This supersedes conditional Parts 21.2/21.3 and their deliverables. No new dependency, migration, permission or setting is required. No new tests for prose-only changes. Manual lab requirements will be recorded honestly if unavailable.


2026-10-17 scope steering: User questioned reporting depth and requested a comparison with Nagios first. PR creation is held pending that comparison and scope choice. Source comparison confirms missing state-duration breakdowns, outage interval tables, maintenance accounting, reporting timelines, alert histograms and top producers. Service reports use snapshots while host availability uses archive durations. These are proposed follow-up requirements, not silently added to #134. Official Core 4.5.11 sources consulted: cgi/avail.c, histogram.c and summary.c in NagiosEnterprises/nagioscore. No availability target is wanted.

Verification started: `scripts/verify.sh all > /tmp/issue-134-all.log 2>&1` in exec session 76428; still running at last inspection, no failure then (backend at 17%). Do not claim green. Dependencies are isolated in this worktree. VM preflight and status passed unrestricted; existing appliance started with `scripts/vmlab up` for read-only report inspection. CUA reports no available apps/browsers, so manual browser checks were not performed. No guest sync, reset, redeploy, scan, or target mutation performed. Returning appliance to its original powered-off state.


Planning completed: docs/plans/Service_Reports_Nagios_Availability_Plan.md. Official Core 4.5.11 archivejson source supports service availability in bulk, returning host_name/description, state durations and indeterminate/scheduled durations but no live metadata. Plan includes an installed-Core contract gate, duration-weighted grouping, unknown-versus-missing distinction, direct bulk current-status metadata, explicit error behavior, API/UI/export updates and acceptance evidence. No application code changed.

Earlier full verification completed with 3985 backend passes, 14 skips, five failures and one error caused by denied socket creation/DNS in the former sandbox. Full all was not green and frontend stage was not reached. Docs stage independently passes on the plan. Appliance shutdown completed; `scripts/vmlab preflight` confirms poweroff and exclusive control. No manual browser report pass is claimed.
