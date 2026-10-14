# Issue #129: System Refinement Harden NCPA Deployment With Per-Device Port, Cleanup Action and Macro Secrets

Branch: `issue-129-ncpa-hardening`
Status: in-progress

## Finish condition

Copied from issue sections E, F and H; tick only with observed proof.

### E. Acceptance criteria
- [x] Existing-device Nagios config remains unchanged after port migration. (`test_backfilled_port_preserves_existing_ncpa_config`, generated-at timestamp normalized)
- [x] Non-default deployed port is used for monitoring, probes and relocation. (`test_alternate_listener_port_is_used_in_check`, `test_disk_probe_uses_stored_port`, `test_reachability_uses_explicit_installed_port`, `test_uses_stored_port_for_known_agent`, `test_alternate_port_is_swept_and_probed`)
- [x] Missing stored port falls back to NCPA_PORT. (`test_deployed_port_resolution_uses_stored_port_and_default`, `test_only_deployed_agents_with_latest_deployment`)
- [x] Migration downgrades cleanly. (`test_ncpa_port_migration_backfills_deployed_only_and_downgrades`)
- [ ] Failed-install cleanup removes key, rule, helper and optionally account; reports steps.
- [x] Cleanup refuses healthy deployment, untrusted device and running deployment. (`TestCleanup.test_refuses_untrusted_healthy_and_running`)
- [x] Changed host key stops cleanup before any command runs. (`test_changed_host_key_stops_before_cleanup`, `test_cleanup_connection_failure_runs_no_commands`)
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
- [x] API endpoint with docstring and permission check. (`TestCleanup.test_requires_login_and_permission`, route catalog)
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

1. [x] Port tracking: tests in `server/tests/unit/test_ncpa.py`, `test_ncpa_deployment_runs.py`, `test_ncpa_identity.py`, `test_port_lifecycle.py`, `test_create_host_cfg.py`, migration tests; model `server/app/system_models.py`, migration `server/migrations/versions/`, deployment `server/app/ncpa_deployment/ncpa_deployment.py`, discovery `server/app/network_discovery/{plugin_registry,ncpa_relocation,identity_probes,port_lifecycle,create_host_cfg}.py`.
2. [x] Cleanup backend: tests in `server/tests/unit/test_ncpa_deployment_runs.py`, `test_ncpa_command_logging.py`, `test_ncpa.py`; `server/app/api/system/ncpa_deployment.py`, `server/app/ncpa_deployment/ncpa_deployment.py`, activity/status integration. Explicit injection/secret review before touching these sensitive modules.
3. [ ] Cleanup UI: tests under `client/src/test/NcpaDeploymentPage.test.tsx` and `NcpaDeployWizard.test.tsx`; `client/src/pages/NcpaDeploymentPage.tsx`, `client/src/components/ncpa-deployment/`, `client/src/lib/ncpaDeploymentApi.ts`, `client/src/types/ncpaDeployment.ts`.
4. [ ] Macro secrets: tests `server/tests/unit/{test_create_host_cfg,test_custom_checks,test_ncpa,test_status}.py` and new resource-macro tests; `server/app/network_discovery/{resource_macros,create_host_cfg,plugin_registry,custom_checks}.py`, deployment/integration permissions contract. Review injection, process exposure and resource-file ownership with a person before code.
5. [ ] Document new behavior, security/installer assumptions, user Help and upgrade guidance in `spec files/{Data_Model_and_Integrations,Backend_Modules_and_Routes,Frontend_Modules_and_Routes,Engineering_Standards,Implementation_Status}.md`, appropriate Help/Admin manual, README if configuration changes; run docs verification.
6. [ ] Re-read issue and prove every E/F/H item; run `scripts/verify.sh all`, record output and sanitized lab evidence in `docs/test-runs/`, finish PR template and request review. No live tests/labs without explicit authorization under workflow hard limits.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 (partial) | Added nullable Port model, generated/reviewed multi-bind migration with deployed-row backfill, fallback and protection/planning tests; remaining port consumers not yet wired | `cd server && .venv/bin/python -m pytest tests/unit/test_ncpa.py tests/unit/test_port_lifecycle.py tests/unit/test_create_host_cfg.py tests/unit/test_ncpa_identity.py tests/unit/test_ncpa_deployment_runs.py -q`; `scripts/verify.sh backend` | Focused 211 passed; backend printed 2581 passed/14 skipped but shell timed out at 300 s after pytest output. Step 1 remains unticked. |
| 2 (partial) | Added alternate-port identity probe test and lookup, preserved standard-port no-extra-query path; updated legacy probe fixture to use database | `cd server && .venv/bin/python -m pytest tests/unit/test_ncpa_identity.py::TestCollectIdentifiers -q` | 5 passed; step 1 remains unticked pending relocation, reachability and migration roundtrip. |
| 3 (partial) | Added explicit reachability/disk probe port tests, stored port at install, suppressed potentially secret-bearing request exception log | `cd server && .venv/bin/python -m pytest tests/unit/test_ncpa_identity.py::test_disk_probe_uses_stored_port tests/unit/test_ncpa_identity.py::test_reachability_uses_explicit_installed_port tests/unit/test_ncpa_identity.py::TestInstallNcpa -q`; focused install assertions | 8 passed; install port assertions 2 passed. Step 1 remains unticked. |
| 4 (partial) | Swept per distinct candidate port, probed matching certificate on that port, preserved legacy default sweep call; repaired optional disk getter compatibility | `cd server && .venv/bin/python -m pytest tests/unit/test_ncpa_identity.py tests/unit/test_ncpa_deployment_runs.py tests/unit/test_port_lifecycle.py tests/unit/test_ncpa.py tests/unit/test_create_host_cfg.py -q` | 216 passed. Step 1 remains unticked: migration roundtrip, non-default service rendering and complete stage check still needed. |
| 5 (partial) | Added migration backfill/downgrade subprocess and non-default check rendering test | `cd server && .venv/bin/python -m pytest tests/unit/test_create_host_cfg.py::TestNcpaHost::test_alternate_listener_port_is_used_in_check tests/unit/test_ncpa_port_migration.py -q`; `scripts/verify.sh backend` | Focused 2 passed; backend green: 2588 passed, 14 skipped (301 s). Step 1 remained unticked pending legacy config equivalence. |
| 6 | Tested pre/backfilled port output equality (ignoring generated timestamp); completed port-tracking step | `cd server && .venv/bin/python -m pytest tests/unit/test_create_host_cfg.py::TestCreateHostCfgFile::test_backfilled_port_preserves_existing_ncpa_config -q`; `scripts/verify.sh backend` | 1 passed; backend green, 2588 passed/14 skipped; spec documentation remains plan step 5. |
| 7 | Added failed-only cleanup route, SSH fingerprint recheck, fixed-path/bootstrap artifact removal with quoted key, optional account removal gated on prior success, suppressed remote output, activity/status recording and API documentation. Reviewed shell construction and secret-bearing logging. | `cd server && .venv/bin/python -m pytest tests/unit/test_ncpa.py::TestCleanup tests/unit/test_ncpa_command_logging.py -q`; `scripts/verify.sh backend` | Focused 25 passed; backend green, 2599 passed/14 skipped. No live cleanup yet; UI and VM verification remain. |

## State for the next session

- Last check run (exact command): `scripts/verify.sh backend`
- Result (first failing lines, or "green"): green, 2599 passed, 14 skipped.
- Hypothesis: Cleanup route/worker pass isolated checks; UI is the first unticked step and VM evidence is still pending.
- Next action (one specific step, not "continue"): Add an interaction test for failed-only cleanup in `client/src/test/NcpaDeploymentPage.test.tsx`, then implement the cleanup dialog and API wrapper.

## Decisions and notes

- `gh issue view 129` fails because GitHub's classic projectCards GraphQL field is deprecated; `gh issue view 129 --json number,title,body,comments,labels,state` works. The finish condition explicitly includes all E, F and H items; C/D/G map to those items in the table above. No unaccounted requirement identified.
- Specification touched: `Data_Model_and_Integrations.md` NCPA deployment and discovery mapping; `Backend_Modules_and_Routes.md` NCPA API; `Frontend_Modules_and_Routes.md` NCPA page; `Engineering_Standards.md` sensitive modules; `Implementation_Status.md` known gaps.
- Existing `Data_Model_and_Integrations.md` describes a single configured NCPA port and literal custom-check passwords as current behavior; `Implementation_Status.md` identifies these as gaps, so these are intentional behavior changes, not silent drift.
- Human review needed per `.agent/workflows/work-issue.md` §4: this change touches sensitive `app/network_discovery/`, `app/ncpa_deployment/` and command execution, requires migration of existing data, and may require installer privilege changes for atomic nagios-owned resource.cfg updates. Decide installer ownership/write mechanism and approve the privileged cleanup/macro and migration design; do not improvise privileged writes or claim live evidence.
- Owner approved VM usage and requested comparing VM and Docker environments first. Read-only comparison: both running, Ubuntu 22.04.5, Python 3.14.8, `resource.cfg` nagios:nagios 660, `hosts.cfg` pinpoint:nagios 664. Docker Nagios reports 4.5.11; VM lab user cannot execute Nagios binary directly (`Permission denied`), so VM version not independently confirmed. Docker uses supervisord and shimmed sudo/systemctl; VM uses systemd and installer-built permissions. Docker targets use supervisord/no init and cannot test NCPA install. Docker network 10.78.0.0/24, VM targets 10.77.0.0/28. `scripts/vmlab status` warns VM base snapshot hash 11a026f00fff differs from current installer base hash b4dc27490318; do not replace a running VM snapshot without owner coordination. Use VM for NCPA cleanup and real permission verification, Docker only for config logic if needed. No lab mutated in this comparison.
- On resumption, owner additionally approved sensitive cleanup, macro-writer and existing-data migration work. Review command construction and secret exposure explicitly; installer privileges remain a separate repository contract and must be reported if an external change is needed. VM usage is approved for this session.
- `flask db upgrade --multidb` and `flask db migrate --multidb` are rejected by the installed Flask-Migrate CLI (no such option); `flask db upgrade` and `flask db migrate` invoke both bind branches via this repository's multi-bind env. Autogenerated migration contained only `NCPA_DEPLOYMENT.Port`; added a deployed-row backfill by hand after review. Generation used throwaway system DB and configured history bind, not production data.
- Sensitive path review pending for cleanup/macro: no untrusted shell interpolation, no secret-bearing logs or responses, preserve fingerprint and Nagios validation. No VM tests performed yet.
