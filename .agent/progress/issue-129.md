# Issue #129: System Refinement Harden NCPA Deployment With Per-Device Port, Cleanup Action and Macro Secrets

Branch: `issue-129-ncpa-hardening`
Status: blocked

## Finish condition

Copied from issue sections E, F and H; tick only with observed proof.

### E. Acceptance criteria
- [ ] Existing-device Nagios config remains unchanged after port migration.
- [ ] Non-default deployed port is used for monitoring, probes and relocation.
- [ ] Missing stored port falls back to NCPA_PORT.
- [ ] Migration downgrades cleanly.
- [ ] Failed-install cleanup removes key, rule, helper and optionally account; reports steps.
- [ ] Cleanup refuses healthy deployment, untrusted device and running deployment.
- [ ] Changed host key stops cleanup before any command runs.
- [ ] No credentials in responses, logs or database.
- [ ] Permitted user cleans failed device with confirmed host key and credentials, seeing step results.
- [ ] Healthy deployed device has no cleanup action.
- [ ] Credentials cleared after request.
- [ ] Existing wizard and page tests pass unchanged.
- [ ] No NCPA token/custom-check password in hosts.cfg, process list or snapshot.
- [ ] NCPA services have same lab results as before.
- [ ] resource.cfg content outside owned block, owner and mode preserved.
- [ ] hosts.cfg mode 0640 and readable by Nagios.
- [ ] Device removal reclaims macro slot; limit errors without invalid config.
- [ ] Failed validation restores resource.cfg and hosts.cfg.

### F. Required deliverables
- [ ] Updated application source (section C).
- [ ] API endpoint with docstring and permission check.
- [ ] Multi-database reversible migration and sync-permissions note if applicable.
- [ ] Updated frontend components, types and routes.
- [ ] Unit tests for modified logic.
- [ ] Frontend interaction tests under client/src/test/.
- [ ] Integration/regression workflow tests from section G.
- [ ] Updated Data Model, Backend, Frontend, Engineering Standards and Implementation Status specs.
- [ ] Updated Help text and Admin secrets-storage note.
- [ ] verify.sh all output attached to PR and sanitized docs/test-runs/ report.

### H. Definition of done
- [ ] All mandatory acceptance criteria satisfied.
- [ ] Required functionality works as specified.
- [ ] No unintentional regressions.
- [ ] Applicable edge cases handled.
- [ ] Existing architectural patterns followed.
- [ ] No unnecessary duplicate functionality.
- [ ] Relevant lint/static analysis passes.
- [ ] No unresolved critical defects.
- [ ] Required automated tests added/updated.
- [ ] Applicable automated tests pass.
- [ ] Relevant integration/regression tests pass.
- [ ] Test/verification evidence attached to PR.
- [ ] User inputs and configuration validated.
- [ ] Authorization enforced.
- [ ] Sensitive data handled securely.
- [ ] Errors handled safely.
- [ ] Performance/reliability requirements met.
- [ ] Technical docs updated.
- [ ] User docs updated.
- [ ] New config parameters documented.
- [ ] Deployment/migration steps documented.
- [ ] PR references #129.
- [ ] PR describes implementation and tests.
- [ ] Required CI checks pass.
- [ ] Required reviewer approvals obtained.
- [ ] Blocking review comments resolved.
- [ ] All applicable acceptance and deliverables complete.

Requirement coverage (each issue requirement maps to E/F/H; proof pending):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| A: global port, failed cleanup, UI gap, literal secrets | E: port, cleanup, UI, secrets | Migration/unit/UI/lab checks in G (pending) |
| C Backend 1–4: port tracking/backfill, all consumers, protected mapping, re-port decision | E: existing config, non-default port, fallback, downgrade; H: config documented | Port/migration and lifecycle tests (pending) |
| C Backend 5–7: trusted cleanup, report, refusal, audit/status | E: cleanup removal/refusals/key/no credentials; F: endpoint | SSH/route security tests (pending) |
| C Backend 8–12: macro writer, slots, modes, limit, rollback | E: secrecy/ownership/mode/slots/rollback; F: source, docs | Writer/config/lab tests (pending) |
| C Frontend 1–3: action, results/status, credential clearing | E: UI action/visibility/clearing; F: frontend/tests | Frontend interaction tests (pending) |
| D: unchanged legacy output, security review, equivalent checks, snapshot stripping, validation, permissions, migration, reliability | E: legacy output/secrecy/result; H: security/quality/reliability | Regression/security/upgrade/lab checks (pending) |
| F: source, API, migration, tests, docs, lab report and verify output | F: corresponding deliverable checkboxes | File/command/report evidence (pending) |
| G: unit, regression, upgrade and live lab workflows | F: integration/regression and evidence; H: testing | Runs named in G (pending) |
| H: quality, review, CI and documentation | H: corresponding checkboxes | CI/PR/reviewer evidence (pending) |

## Plan

1. [ ] Port tracking: tests in `server/tests/unit/test_ncpa.py`, `test_ncpa_deployment_runs.py`, `test_ncpa_identity.py`, `test_port_lifecycle.py`, `test_create_host_cfg.py`, migration tests; model `server/app/system_models.py`, migration `server/migrations/versions/`, deployment `server/app/ncpa_deployment/ncpa_deployment.py`, discovery `server/app/network_discovery/{plugin_registry,ncpa_relocation,identity_probes,port_lifecycle,create_host_cfg}.py`.
2. [ ] Cleanup backend: tests in `server/tests/unit/test_ncpa_deployment_runs.py`, `test_ncpa_command_logging.py`, `test_ncpa.py`; `server/app/api/system/ncpa_deployment.py`, `server/app/ncpa_deployment/ncpa_deployment.py`, activity/status integration. Explicit injection/secret review before touching these sensitive modules.
3. [ ] Cleanup UI: tests under `client/src/test/NcpaDeploymentPage.test.tsx` and `NcpaDeployWizard.test.tsx`; `client/src/pages/NcpaDeploymentPage.tsx`, `client/src/components/ncpa-deployment/`, `client/src/lib/ncpaDeploymentApi.ts`, `client/src/types/ncpaDeployment.ts`.
4. [ ] Macro secrets: tests `server/tests/unit/{test_create_host_cfg,test_custom_checks,test_ncpa,test_status}.py` and new resource-macro tests; `server/app/network_discovery/{resource_macros,create_host_cfg,plugin_registry,custom_checks}.py`, deployment/integration permissions contract. Review injection, process exposure and resource-file ownership with a person before code.
5. [ ] Document new behavior, security/installer assumptions, user Help and upgrade guidance in `spec files/{Data_Model_and_Integrations,Backend_Modules_and_Routes,Frontend_Modules_and_Routes,Engineering_Standards,Implementation_Status}.md`, appropriate Help/Admin manual, README if configuration changes; run docs verification.
6. [ ] Re-read issue and prove every E/F/H item; run `scripts/verify.sh all`, record output and sanitized lab evidence in `docs/test-runs/`, finish PR template and request review. No live tests/labs without explicit authorization under workflow hard limits.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|

## State for the next session

- Last check run (exact command): `git fetch -q origin && git checkout -b issue-129-ncpa-hardening origin/main && cat AGENTS.md`
- Result (first failing lines, or "green"): green
- Hypothesis: Work requires the sensitive-module review and existing-data migration decision mandated by workflow stop conditions.
- Next action (one specific step, not "continue"): Ask the owner to approve the privileged resource.cfg writer/installer permission approach, existing-data migration and sensitive-module security review, then resume the first port-tracking test.

## Decisions and notes

- `gh issue view 129` fails because GitHub's classic projectCards GraphQL field is deprecated; `gh issue view 129 --json number,title,body,comments,labels,state` works. The finish condition explicitly includes all E, F and H items; C/D/G map to those items in the table above. No unaccounted requirement identified.
- Specification touched: `Data_Model_and_Integrations.md` NCPA deployment and discovery mapping; `Backend_Modules_and_Routes.md` NCPA API; `Frontend_Modules_and_Routes.md` NCPA page; `Engineering_Standards.md` sensitive modules; `Implementation_Status.md` known gaps.
- Existing `Data_Model_and_Integrations.md` describes a single configured NCPA port and literal custom-check passwords as current behavior; `Implementation_Status.md` identifies these as gaps, so these are intentional behavior changes, not silent drift.
- Human review needed per `.agent/workflows/work-issue.md` §4: this change touches sensitive `app/network_discovery/`, `app/ncpa_deployment/` and command execution, requires migration of existing data, and may require installer privilege changes for atomic nagios-owned resource.cfg updates. Decide installer ownership/write mechanism and whether the issue's lab requirements explicitly authorize running VM/Docker labs in this session; do not improvise privileged writes or claim live evidence.
