# Issue #134: Reconcile Reports documentation

Branch: `issue-134-reports-documentation`
Status: in-progress

## Finish condition

- [x] E / Part 21.1: both inventories accurately list all six views.
- [x] E / Part 21.1: each view names its API route.
- [x] E / Part 21.1: `scripts/verify.sh docs` passes.
- [x] C / Part 21.1: record displayed fields, period handling and export support; file defects separately.
- [x] F/G/H applicable evidence: full verification and sanitized report, including six-view appliance checks.

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
2. [x] Recheck source mappings; correct export heading in spec files/Frontend_Modules_and_Routes.md and stale target-decision references in docs/issues/README.md and docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md; run docs/all verification, record docs/test-runs evidence and the six-view browser result; report defects separately.
3. [x] On user steering, write docs/plans/Service_Reports_Nagios_Availability_Plan.md for the two service reports; do not implement or open the documentation PR until follow-up scope is settled.
4. [ ] Re-read #134, prove applicable finish conditions, remove progress file when complete and open PR using the template; inspect CI.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 2 | Corrected exact column labels/decision references and recorded real six-view/CSV/full-suite evidence | scripts/verify.sh all; Playwright /tmp/issue-134-reports-browser.cjs | green: 3991 backend, 912 frontend; six views and six CSV exports passed |
| resumed | Pulled issue branch, re-read #134 and reran last check | scripts/verify.sh docs | green; full suite running |
| Planning | Drafted the user-requested Nagios-backed service-report plan | scripts/verify.sh docs | green; no product implementation |
| 1 | Source audit and documentation reconciliation; recorded rejection of targets | scripts/verify.sh docs | green |
| Intake | Scope narrowed by explicit user decision | gh issue view 134 --json number,title,body,comments,state | Part 21.1 remains; targets rejected |

## State for the next session

- Last check run (exact command): scripts/verify.sh all > /tmp/issue-134-resume-all.log 2>&1
- Result (first failing lines, or "green"): green; 3991 backend passed / 14 skipped; 912 frontend passed; build/lint passed (31 warnings)
- Hypothesis: all applicable documentation scope is proven, including the user-authorized Playwright six-view/CSV checks. No application behavior changed.
- Next action (one specific step, not "continue"): Re-read #134 for final requirement coverage, remove the progress file, push the docs/evidence change and open its PR; monitor required CI.

## Decisions and notes

The user explicitly decided: "pinpoint does not need the feature, we only need to show the measured uptime, which I think it already does". This supersedes conditional Parts 21.2/21.3 and their deliverables. No new dependency, migration, permission or setting is required. No new tests for prose-only changes. Manual lab requirements will be recorded honestly if unavailable.


2026-10-17 scope steering: User questioned reporting depth and requested a comparison with Nagios first. PR creation is held pending that comparison and scope choice. Source comparison confirms missing state-duration breakdowns, outage interval tables, maintenance accounting, reporting timelines, alert histograms and top producers. Service reports use snapshots while host availability uses archive durations. These are proposed follow-up requirements, not silently added to #134. Official Core 4.5.11 sources consulted: cgi/avail.c, histogram.c and summary.c in NagiosEnterprises/nagioscore. No availability target is wanted.

Verification started: `scripts/verify.sh all > /tmp/issue-134-all.log 2>&1` in exec session 76428; still running at last inspection, no failure then (backend at 17%). Do not claim green. Dependencies are isolated in this worktree. VM preflight and status passed unrestricted; existing appliance started with `scripts/vmlab up` for read-only report inspection. CUA reports no available apps/browsers, so manual browser checks were not performed. No guest sync, reset, redeploy, scan, or target mutation performed. Returning appliance to its original powered-off state.


Planning completed: docs/plans/Service_Reports_Nagios_Availability_Plan.md. Official Core 4.5.11 archivejson source supports service availability in bulk, returning host_name/description, state durations and indeterminate/scheduled durations but no live metadata. Plan includes an installed-Core contract gate, duration-weighted grouping, unknown-versus-missing distinction, direct bulk current-status metadata, explicit error behavior, API/UI/export updates and acceptance evidence. No application code changed.

Earlier full verification completed with 3985 backend passes, 14 skips, five failures and one error caused by denied socket creation/DNS in the former sandbox. Full all was not green and frontend stage was not reached. Docs stage independently passes on the plan. Appliance shutdown completed; `scripts/vmlab preflight` confirms poweroff and exclusive control. No manual browser report pass is claimed.


2026-10-17: Owner approved turning the service-report plan into a separate implementation issue and explicitly required removal of snapshot counts. The plan now mandates removal from both service-report payloads (including nested instances), types, UI, help and exports, with absence assertions; it forbids hidden count aliases or reusing count fields for seconds. Stored snapshots/general polling stay outside scope. `scripts/verify.sh docs` passes. Next publication action: create the approved follow-up issue, record its URL and checkpoint; no application implementation in this turn.

Created approved follow-up implementation issue: https://github.com/esfen14/Pinpoint/issues/198. Its self-contained body includes the complete plan, explicit snapshot-count removal, finish conditions, deliverables, and CI/live comparison gates. #134 remains the separate documentation issue. No product changes made.


2026-10-17 reporting revision: Owner requested a Nagios-aligned report revision plan with citations and UI planning, tagged low-priority/enhancement/web-interface. Drafted docs/plans/Reports_Revision_Nagios_Alignment_Plan.md, citing official Core CGI docs and pinned 4.5.11 availability/trends/summary/histogram source. Scope preserves six reports, adds availability detail/timeline, summary and histogram, defines UI/export/source/completeness/verification requirements, and depends on #198. No app implementation. `scripts/verify.sh docs` passes. Publish as a separate implementation backlog issue using existing `Low Priority`, `enhancement`, `web-interface` labels.

Filed reporting revision plan as https://github.com/esfen14/Pinpoint/issues/199 with Low Priority, enhancement and web-interface labels. Full plan/citations/UI wireframe/checklist are self-contained in the issue. #198 is its service-source dependency. No product implementation or PR in this turn.

Resume decision: user asked to complete #134 after follow-up issues were filed. Resume the existing unticked verification step. Source reinspection found the Network Services export uses `Total Instances`, so fix that exact documentation heading. Update only the stale target-decision entries in the originating plan/index so they no longer invite implementing rejected targets. Browser verification remains pending because CUA has no enabled browser; clarification requested asynchronously.


Live verification resolved: owner explicitly instructed Playwright. After matching vmlab's pre-config credential-state resolution (rather than the config override), login succeeded without account changes. Six report APIs returned populated 200 responses. Playwright opened all six views and checked all six CSV downloads' documented headers/content. Initial Notifications locator matched the header bell; the final complete repeat with a text-bearing-tab selector passed. Appliance commit 82ba9ce9 and Core4.5.11; all seven relevant report source files match this branch, tracked guest worktree clean. Documented Host Availability's existing on-screen Snapshots column and its known-seconds meaning. No product code changed; snapshot removal remains #198/#199. Full suite currently progressing past 88%; report still provisional until exit.

Completed verification round: scripts/verify.sh all exited 0. Final issue body/comments re-read in /tmp/issue-134-final-issue.json; no new requirements/comments. Parts 21.2/21.3 are excluded by explicit owner decision; unchanged application means source/API/migration/help deliverables for those parts are not applicable. R134-DOCS, R134-ALL and the six live view+CSV cases are recorded in the sanitized report. XLS/PDF execution and interactive custom-date entry were not exercised (source inspection only); neither is an additional Part21.1 live acceptance gate. Existing lint warnings are not changed. Appliance restored to original poweroff state through guarded down.
