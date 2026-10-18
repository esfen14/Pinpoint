# Issue #234: Investigate NCPA resource-helper rejection, conflicting deployment results, and missing metrics

Branch: `issue-234-ncpa-helper`
Status: blocked

## Finish condition

- [ ] Identify and document the root cause with application/installer revisions and helper diagnostics, keeping secrets private.
- [ ] Resolve the supported installer/deployment dependency or validation failure while preserving restricted writes.
- [ ] Make the run and per-device UI outcomes clearly describe installation versus monitoring-attachment failures.
- [ ] Verify that a supported deployment produces live NCPA metrics in Network Health.
- [ ] Verify failure reporting when agent installation succeeds but the protected configuration stage is rejected.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Diagnose exact root cause; record app/installer revisions and helper diagnostics without secrets | Root cause documented | Reproduction report with revision IDs, helper/sudo diagnostics and sanitized output |
| Resolve supported installer/deployment dependency or validation failure, retaining restricted writes | Dependency/failure fixed | Helper contract tests and supported installer deployment check; resource boundary/security tests |
| Distinguish installation success from monitoring/configuration attachment result in run and device UI | UI outcomes clear | Backend result/API tests and frontend tests for partial success and attachment failure |
| Supported deployment yields live NCPA metrics in Network Health | Live metrics verified | QA deployment plus Nagios/Network Health observation recorded in test-run report |
| Protected configuration rejection after successful installation is reported accurately | Failure reporting verified | Backend test with helper rejection, API/run assertion and UI rendering check |

## Plan

1. [ ] Reconcile the protected-helper installer contract and diagnose the current rejection without exposing secrets; inspect NCPA deployment, resource helper, and Network Health paths. Files: `server/app/network_discovery/resource_macros.py`, `server/app/network_discovery/create_host_cfg.py`, `server/app/ncpa_deployment/ncpa_deployment.py`, `server/app/system_models.py`, `client/src/components/ncpa-deployment/`, `client/src/pages/NcpaDeploymentPage.tsx`, `server/tests/plans/`, `docs/test-runs/`.
2. [ ] Add regression tests that separate successful agent installation from failed monitoring attachment and verify sanitized helper diagnostics. Files: `server/tests/unit/test_resource_macros.py`, `server/tests/unit/test_create_host_cfg.py`, `server/tests/unit/test_ncpa_deployment_runs.py`, relevant frontend test files.
3. [ ] Implement the smallest supported fix while preserving helper authorization and resource-file ownership/mode safeguards. Files: source files identified in step 1 and, only if required and in scope, the paired installer dependency.
4. [ ] Update deployment UI/API behavior and specifications to describe installation and monitoring attachment as separate outcomes. Files: relevant files under `client/src/components/ncpa-deployment/`, `server/app/api/system/ncpa_deployment.py`, `spec files/Backend_Modules_and_Routes.md`, `spec files/Frontend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, `spec files/Implementation_Status.md`.
5. [ ] Verify targeted tests and required repository stages, then run supported live deployment/Network Health checks and record sanitized evidence. Files: `docs/test-runs/` and verification outputs.

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|
| Plan | Read issue, routed specs and source leads; created this plan | `gh issue view 234 --json number,title,body,comments,state`; source/spec inspection | Acceptance criteria are explicit; prior missing-helper report is historical context, not fresh reproduction |

## State for the next session

- Last check run (exact command): `git status --short --branch`
- Result (first failing lines, or "green"): clean `issue-234-ncpa-helper` branch at `origin/main` before adding this progress record.
- Hypothesis: the issue may be the known missing installer helper/sudo rule, but the report expressly says this is not established for the current environment. Current `add_ncpa_port` marks the run failed after configuration apply failure while per-device install results remain Success, so the UI needs stage-aware outcomes.
- Next action (one specific step, not "continue"): obtain the required security review/decision for modifying the protected resource helper/configuration path, then inspect the paired installer's current helper contract and capture fresh, sanitized target diagnostics.

## Decisions and notes

- Do not log or return helper stdout/stderr if it can contain secrets or unsafe paths; diagnostics must be sanitized and stage-specific.
- `Engineering_Standards.md` explicitly classifies `app/network_discovery/` and `app/ncpa_deployment/` as sensitive and requires injection/secret-exposure review. The work-issue procedure says to stop for a person when a change touches a sensitive module; no implementation change has been made pending that review/decision.
- Person needed: review and authorize the security-sensitive helper/configuration changes for this issue, including the planned sanitized diagnostics and how a fresh target reproduction can be performed. The workflow explicitly lists sensitive modules as a stop condition.
- The installer is maintained in a separate repository. The issue links PR #7 as an investigation lead, but does not establish that its current revision is the cause.
