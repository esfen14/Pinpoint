# Issue #234: Investigate NCPA resource-helper rejection, conflicting deployment results, and missing metrics

Branch: `issue-234-ncpa-helper`
Status: in-progress

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

1. [x] Reconcile the protected-helper installer contract and diagnose the current rejection without exposing secrets; inspect NCPA deployment, resource helper, and Network Health paths. Files: `server/app/network_discovery/resource_macros.py`, `server/app/network_discovery/create_host_cfg.py`, `server/app/ncpa_deployment/ncpa_deployment.py`, `server/app/system_models.py`, `client/src/components/ncpa-deployment/`, `client/src/pages/NcpaDeploymentPage.tsx`, `server/tests/plans/`, `docs/test-runs/`.
2. [x] Add regression tests that separate successful agent installation from failed monitoring attachment and verify sanitized helper diagnostics. Files: `server/tests/unit/test_resource_helper_client.py`, `server/tests/unit/test_plugin_reconcile.py`, `server/tests/unit/test_ncpa_deployment_runs.py`, `client/src/test/NcpaDeploymentPage.test.tsx`, `client/src/test/NcpaDeploymentNotification.test.tsx`.
3. [x] Implement the smallest supported fix while preserving helper authorization and resource-file ownership/mode safeguards. Files: `server/app/network_discovery/resource_macros.py`, `server/app/network_discovery/create_host_cfg.py`, `client/src/components/ncpa-deployment/DeploymentBadges.tsx`, `client/src/components/ncpa-deployment/DeploymentRunDrawer.tsx`, `client/src/components/ncpa-deployment/DeploymentRunBanner.tsx`, `client/src/components/ncpa-deployment/DeploymentStatusItem.tsx`, `client/src/types/ncpaDeployment.ts`.
4. [x] Update deployment UI/API behavior and specifications to describe installation and monitoring attachment as separate outcomes. Files: relevant files under `client/src/components/ncpa-deployment/`, `server/app/api/system/ncpa_deployment.py`, `spec files/Backend_Modules_and_Routes.md`, `spec files/Frontend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, `spec files/Implementation_Status.md`.
5. [ ] Finish the repository gates, record final results, then complete acceptance only if the originating helper rejection is diagnosed. Files: `docs/test-runs/` and verification outputs.

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|
| Plan | Read issue, routed specs and source leads; created this plan | `gh issue view 234 --json number,title,body,comments,state`; source/spec inspection | Acceptance criteria are explicit; prior missing-helper report is historical context, not fresh reproduction |
| Resume | Owner approved the security-sensitive plan; reopened work | `gh pr view 7 --repo lorraine-pangilinan/PinPoint-Installer --json number,title,body,state,headRefName,headRefOid,baseRefName`; `scripts/vmlab status`; `scripts/vmlab preflight` | Installer PR head is `b166953d2e7e5b4bae12bf723712224cc97fae94`; local installer main does not contain the helper; QA VM control preflight passed |
| 1 | Reconciled helper contract and VM state; completed a real deployment and added sanitized evidence report | `scripts/vmlab ncpa 10.77.0.3`; authenticated `/api/system/network-health/services` detail and `/network-health/trends`; SSH metadata/sudo checks | Deployment and live metrics passed; previously reported helper rejection not reproduced; report records historical missing-helper diagnosis separately |
| 2 | Added helper rejection and attachment-stage regression coverage; implemented fixed diagnostics, per-device stage reporting and clearer run/device labels | Red first: targeted tests failed because helper errors were generic, device errors stayed null and UI claimed checks existed. Green: `server/.venv/bin/python -m pytest server/tests/unit/test_resource_helper_client.py server/tests/unit/test_plugin_reconcile.py::TestNcpaAndInventory server/tests/unit/test_ncpa_deployment_runs.py -q` (65 passed); `npm test -- --run src/test/NcpaDeploymentPage.test.tsx src/test/NcpaDeploymentNotification.test.tsx` (16 passed) | Protected boundary and install outcome preserved; safe helper guidance and UI stage separation verified |
| 3 | Updated the data/API/UI behavior specs, implementation status, and test-run index/report; completed repository verification | `scripts/verify.sh backend` (4,333 passed, 14 skipped); `scripts/verify.sh frontend` (1,016 passed, build passed, lint 0 errors/33 warnings); `scripts/verify.sh all` / docs stage fails in unrelated QA supervisor controller claim tests | Targeted and independent backend/frontend gates pass; docs supervisor test issue and original rejection diagnosis remain outstanding |

## State for the next session

- Last check run (exact command): `scripts/verify.sh all`
- Result (first failing lines, or "green"): backend green (4,333 passed, 14 skipped); frontend green (1,016 passed, build passed, lint 0 errors/33 warnings). Combined docs gate fails in `scripts/test_qa_supervisor.py` with `ValueError: Host controller unavailable, already owned or unsafe`, followed by ledger assertion failures.
- Hypothesis: implementation and live success path are verified, but the exact reported rejection is not reproduced; docs-stage harness failure is unrelated to modified files.
- Next action (one specific step, not "continue"): obtain sanitized helper rejection diagnostics from the originating QA environment, then rerun the applicable live acceptance case.

## Decisions and notes

- Do not log or return helper stdout/stderr if it can contain secrets or unsafe paths; diagnostics must be sanitized and stage-specific.
- `Engineering_Standards.md` explicitly classifies `app/network_discovery/` and `app/ncpa_deployment/` as sensitive and requires injection/secret-exposure review. The owner approved the security-sensitive plan on 2026-10-19.
- The installer is maintained in a separate repository. The issue links PR #7 as an investigation lead, but does not establish that its current revision is the cause.
- Live diagnosis: deployed application files match `4aa4e1eb`; VM base installer stamp is `697869e`; the installed helper hash matches the source from installer PR #7 commit `b166953d2e7e5b4bae12bf723712224cc97fae94`. The earlier missing helper/sudo rule explains that earlier setup only. Current QA helper rejection remains unconfirmed.
