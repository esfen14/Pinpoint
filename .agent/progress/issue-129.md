# Issue #129: System Refinement Harden NCPA Deployment With Per-Device Port, Cleanup Action and Macro Secrets

Branch: `issue-129-ncpa-hardening`
Status: blocked

## Finish condition

Copied from issue sections E, F and H; tick only with observed proof.

### E. Acceptance criteria
- [x] Existing-device Nagios config remains unchanged after port migration. (`test_backfilled_port_preserves_existing_ncpa_config`, generated-at timestamp normalized)
- [x] Non-default deployed port is used for monitoring, probes and relocation. (`test_alternate_listener_port_is_used_in_check`, `test_disk_probe_uses_stored_port`, `test_reachability_uses_explicit_installed_port`, `test_uses_stored_port_for_known_agent`, `test_alternate_port_is_swept_and_probed`)
- [x] Missing stored port falls back to NCPA_PORT. (`test_deployed_port_resolution_uses_stored_port_and_default`, `test_only_deployed_agents_with_latest_deployment`)
- [x] Migration downgrades cleanly. (`test_ncpa_port_migration_backfills_deployed_only_and_downgrades`)
- [x] Failed-install cleanup removes key, rule, helper and optionally account; reports steps. (`TestCleanup.test_success_reports_steps_and_clears_status_without_exposing_credentials`; route implemented in `ncpa_deployment.py` with per-step reporting)
- [x] Cleanup refuses healthy deployment, untrusted device and running deployment. (`TestCleanup.test_refuses_untrusted_healthy_and_running`)
- [x] Changed host key stops cleanup before any command runs. (`test_changed_host_key_stops_before_cleanup`, `test_cleanup_connection_failure_runs_no_commands`)
- [x] No credentials in responses, logs or database. (`test_credentials_never_reach_the_log`; cleanup route suppresses remote output; `test_the_password_is_never_stored_or_returned`)
- [x] Permitted user cleans failed device with confirmed host key and credentials, seeing step results. (`NcpaDeploymentPage` CleanupDialog interaction test; per-step result array in response)
- [x] Healthy deployed device has no cleanup action. (`NcpaDeploymentPage` cleanup interaction test)
- [x] Credentials cleared after request. (`TestCleanup` route finally; frontend interaction asserts cleared fields)
- [x] Existing wizard and page tests pass unchanged. (`scripts/verify.sh frontend`: 554 passed)
- [ ] No NCPA token/custom-check password in hosts.cfg, process list or snapshot. (`test_ncpa_token_absent_from_hosts_cfg`, `test_custom_check_password_absent_from_hosts_cfg`, `test_the_command_in_hosts_cfg_uses_the_decrypted_password` updated; `test_the_whole_file_is_consistent` updated; backend 2644 passed)
- [ ] NCPA services have same lab results as before. (lab verification pending — requires authorized VM run)
- [ ] resource.cfg content outside owned block, owner and mode preserved. (unit: `TestBlockOnlyEditing` all pass; file-mode 0640 set on write; owner `nagios:nagios` is installer responsibility — live lab pending)
- [x] hosts.cfg mode 0640 and readable by Nagios. (`os.chmod(cfg_path, 0o640)` after write; `test_file_mode_is_0640` passes; Nagios readability via group `nagios` confirmed by lab comparison in notes)
- [x] Device removal reclaims macro slot; limit errors without invalid config. (`TestReclaim` all pass; `TestResourceMacroLimitError` all pass — raises `ResourceMacroLimitError` before writing any config)
- [ ] Failed validation restores resource.cfg and hosts.cfg. (`regenerate_and_apply_config_status` backs up resource.cfg before generate and restores it when `_validate_config` returns false; `_apply_new_host_cfg` already rolls back hosts.cfg on reload failure)

### F. Required deliverables
- [x] Updated application source (section C). (`resource_macros.py` new; `create_host_cfg.py`, `config.py`, `ncpa_deployment.py`, `ncpa_deployment.py` route, `NcpaDeploymentPage.tsx`, `CleanupDialog.tsx`, `NcpaDevicesTable.tsx`, `ncpaDeploymentApi.ts`, `ncpaDeployment.ts`, `system_models.py` Port column, migration `7db78f308ee5`)
- [x] API endpoint with docstring and permission check. (`TestCleanup.test_requires_login_and_permission`, route catalog)
- [x] Multi-database reversible migration and sync-permissions note if applicable. (`7db78f308ee5_track_deployed_ncpa_port.py` with backfill and downgrade; no new permission added)
- [x] Updated frontend components, types and routes. (`CleanupDialog`, table, page, typed API wrapper)
- [x] Unit tests for modified logic. (`test_resource_macros.py` 42 tests; `test_create_host_cfg.py` 3 new integration tests; updated `test_custom_checks.py`, `test_custom_checks_config_structure.py`; all in 2644 passed)
- [x] Frontend interaction tests under client/src/test/. (`NcpaDeploymentPage.test.tsx`)
- [ ] Integration/regression workflow tests from section G. (live lab workflows pending authorized run)
- [ ] Updated Data Model, Backend, Frontend, Engineering Standards and Implementation Status specs.
- [ ] Updated Help text and Admin secrets-storage note.
- [ ] verify.sh all output attached to PR and sanitized docs/test-runs/ report.

### H. Definition of done
- [ ] All mandatory acceptance criteria satisfied. (lab items pending)
- [ ] Required functionality works as specified. (all unit/integration tests passing; 2644 passed)
- [ ] No unintentional regressions. (backend 2644 passed/14 skipped; frontend 554 passed)
- [ ] Applicable edge cases handled. (limit error, missing resource.cfg graceful warning, rollback on validation failure, slot stability, reclaim)
- [x] Existing architectural patterns followed. (resource_macros uses same config/app_context pattern; substitution at write time, not in registry)
- [x] No unnecessary duplicate functionality. (no parallel macro system; reuses existing plugin_registry validation)
- [ ] Relevant lint/static analysis passes. (verify.sh all pending)
- [ ] No unresolved critical defects.
- [x] Required automated tests added/updated. (42 new unit tests in test_resource_macros.py; 3 integration tests; 4 existing tests updated)
- [x] Applicable automated tests pass. (2644 passed, 14 skipped)
- [ ] Relevant integration/regression tests pass. (live lab pending)
- [ ] Test/verification evidence attached to PR.
- [x] User inputs and configuration validated. (NAGIOS_RESOURCE_CFG from env; slot limit enforced before any write)
- [x] Authorization enforced. (cleanup route: `require_permission("deploy_ncpa")` + `require_login`)
- [ ] Sensitive data handled securely. (tokens/passwords not in logs, not in responses, not in hosts.cfg; resource.cfg mode 0640)
- [ ] Errors handled safely. (ResourceMacroLimitError raised before write; OSError on chmod/write caught and logged; rollback on validation failure)
- [x] Performance/reliability requirements met. (secrets collected once per generate call; no per-host queries)
- [ ] Technical docs updated.
- [ ] User docs updated.
- [ ] New config parameters documented. (`NAGIOS_RESOURCE_CFG` added to config.py with docstring; README production settings table update pending)
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
| A: global port, failed cleanup, UI gap, literal secrets | E: port, cleanup, UI, secrets | Port/migration ✓; cleanup unit ✓; cleanup UI ✓; macro secrets unit ✓; lab pending |
| C Backend 1–4: port tracking/backfill, all consumers, protected mapping, re-port decision | E: existing config, non-default port, fallback, downgrade; H: config documented | `test_backfilled_port_preserves_existing_ncpa_config`, `test_alternate_listener_port_is_used_in_check`, migration tests ✓ |
| C Backend 5–7: trusted cleanup, report, refusal, audit/status | E: cleanup removal/refusals/key/no credentials; F: endpoint | `TestCleanup` 25 tests ✓; credentials log test ✓ |
| C Backend 8–12: macro writer, slots, modes, limit, rollback | E: secrecy/ownership/mode/slots/rollback; F: source, docs | `TestResourceMacroLimitError`, `TestReclaim`, `TestBlockOnlyEditing`, `TestWriteResourceBlock` ✓; token absent tests ✓; docs pending |
| C Frontend 1–3: action, results/status, credential clearing | E: UI action/visibility/clearing; F: frontend/tests | `NcpaDeploymentPage.test.tsx` 7 tests ✓ |
| D: unchanged legacy output, security review, equivalent checks, snapshot stripping, validation, permissions, migration, reliability | E: legacy output/secrecy/result; H: security/quality/reliability | Regression: 2644 passed ✓; lab pending |
| F: source, API, migration, tests, docs, lab report and verify output | F: corresponding deliverable checkboxes | Source/API/migration/unit tests ✓; docs/lab pending |
| G: unit, regression, upgrade and live lab workflows | F: integration/regression and evidence; H: testing | Unit ✓; lab pending (requires authorized run) |
| H: quality, review, CI and documentation | H: corresponding checkboxes | Code quality ✓; docs/CI/review pending |

## Plan

1. [x] Port tracking: tests in `server/tests/unit/test_ncpa.py`, `test_ncpa_deployment_runs.py`, `test_ncpa_identity.py`, `test_port_lifecycle.py`, `test_create_host_cfg.py`, migration tests; model `server/app/system_models.py`, migration `server/migrations/versions/`, deployment `server/app/ncpa_deployment/ncpa_deployment.py`, discovery `server/app/network_discovery/{plugin_registry,ncpa_relocation,identity_probes,port_lifecycle,create_host_cfg}.py`.
2. [x] Cleanup backend: tests in `server/tests/unit/test_ncpa_deployment_runs.py`, `test_ncpa_command_logging.py`, `test_ncpa.py`; `server/app/api/system/ncpa_deployment.py`, `server/app/ncpa_deployment/ncpa_deployment.py`, activity/status integration. Explicit injection/secret review before touching these sensitive modules.
3. [x] Cleanup UI: tests under `client/src/test/NcpaDeploymentPage.test.tsx` and `NcpaDeployWizard.test.tsx`; `client/src/pages/NcpaDeploymentPage.tsx`, `client/src/components/ncpa-deployment/`, `client/src/lib/ncpaDeploymentApi.ts`, `client/src/types/ncpaDeployment.ts`.
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
| 8 | Added failed/trusted-only table action, ephemeral SSH credential dialog and per-step reporting, typed cleanup API and UI interaction test. | `cd client && npx vitest run src/test/NcpaDeploymentPage.test.tsx && npx tsc --noEmit`; `scripts/verify.sh frontend` | Focused 7 passed; frontend green: 554 passed, build succeeded, lint 0 errors/29 pre-existing warnings. |
| 10 (resumed/audit) | Re-read live issue and re-ran saved backend check; confirmed synthetic whole-string substitution corrupts non-secret metric paths and resource writer changes 0660 to 0640. Reopened macro plan step; corrected process-list security claim. Added failing metadata regression, fixed atomic writer to preserve owner/group/mode using private unique temp files and fail before replacement if ownership cannot be preserved. Documented NAGIOS_RESOURCE_CFG and macro limitation. | focused macro tests; host/custom regression; docs | 44 macro tests and 173 host/custom tests passed; docs passed. Full backend running; security design decision required. |
| 9 | Implemented resource_macros.py (allocate/write_resource_block/read_resource_block/reclaim/restore_resource_cfg/ResourceMacroLimitError); wired collect_ncpa_secrets, collect_custom_check_secrets, build_secret_substitution_map, apply_secret_substitutions into create_host_cfg.py; NCPA token and custom-check passwords replaced by $USERn$ in hosts.cfg, written to resource.cfg block; hosts.cfg now written mode 0640; resource.cfg backed up and restored on validation failure; added NAGIOS_RESOURCE_CFG to config.py; fixed pre-existing `os` module shadow bug in for-loop; updated 4 test files to assert password absent. | `cd server && .venv/bin/python -m pytest tests/unit/test_resource_macros.py tests/unit/test_create_host_cfg.py tests/unit/test_custom_checks.py tests/unit/test_ncpa.py tests/unit/test_status.py -q` then full backend | Focused 270 passed; backend green: 2644 passed, 14 skipped. |

## State for the next session

- Last check run (exact command): `scripts/verify.sh backend > /tmp/issue-129-backend-verification.log 2>&1`
- Result (first failing lines, or "green"): running; focused macro tests 44 passed, host/custom tests 173 passed, docs green. Update when full stage finishes.
- Hypothesis: Prior notes overstated macro completion. Nagios expands USER macros into plugin argv; the required process-list secrecy cannot be satisfied by the current design. Whole-string substitution corrupts unrelated arguments; missing/write-failed resource files still generate unusable macro references; resource rollback covers only validation failure, not apply failure or all config entry points. Real nagios-owned file update may fail ownership preservation under the installer account; do not change installer privileges here.
- Next action (one specific step, not "continue"): Resolve the NCPA/SMB secure-credential-input compatibility blockers documented in docs/plans/Issue_129_Check_Secret_Transport.md, then add process-list regression tests and repair the macro integration/transaction paths.

## Decisions and notes

- `gh issue view 129` fails because GitHub's classic projectCards GraphQL field is deprecated; `gh issue view 129 --json number,title,body,comments,labels,state` works. The finish condition explicitly includes all E, F and H items; C/D/G map to those items in the table above. No unaccounted requirement identified.
- Specification touched: `Data_Model_and_Integrations.md` NCPA deployment and discovery mapping; `Backend_Modules_and_Routes.md` NCPA API; `Frontend_Modules_and_Routes.md` NCPA page; `Engineering_Standards.md` sensitive modules; `Implementation_Status.md` known gaps.
- Existing `Data_Model_and_Integrations.md` describes a single configured NCPA port and literal custom-check passwords as current behavior; `Implementation_Status.md` identifies these as gaps, so these are intentional behavior changes, not silent drift.
- Human review needed per `.agent/workflows/work-issue.md` §4: this change touches sensitive `app/network_discovery/`, `app/ncpa_deployment/` and command execution, requires migration of existing data, and may require installer privilege changes for atomic nagios-owned resource.cfg updates. Decide installer ownership/write mechanism and approve the privileged cleanup/macro and migration design; do not improvise privileged writes or claim live evidence.
- Owner approved VM usage and requested comparing VM and Docker environments first. Read-only comparison: both running, Ubuntu 22.04.5, Python 3.14.8, `resource.cfg` nagios:nagios 660, `hosts.cfg` pinpoint:nagios 664. Docker Nagios reports 4.5.11; VM lab user cannot execute Nagios binary directly (`Permission denied`), so VM version not independently confirmed. Docker uses supervisord and shimmed sudo/systemctl; VM uses systemd and installer-built permissions. Docker targets use supervisord/no init and cannot test NCPA install. Docker network 10.78.0.0/24, VM targets 10.77.0.0/28. `scripts/vmlab status` warns VM base snapshot hash 11a026f00fff differs from current installer base hash b4dc27490318; do not replace a running VM snapshot without owner coordination. Use VM for NCPA cleanup and real permission verification, Docker only for config logic if needed. No lab mutated in this comparison.
- On resumption, owner additionally approved sensitive cleanup, macro-writer and existing-data migration work. Review command construction and secret exposure explicitly; installer privileges remain a separate repository contract and must be reported if an external change is needed. VM usage is approved for this session.
- `flask db upgrade --multidb` and `flask db migrate --multidb` are rejected by the installed Flask-Migrate CLI (no such option); `flask db upgrade` and `flask db migrate` invoke both bind branches via this repository's multi-bind env. Autogenerated migration contained only `NCPA_DEPLOYMENT.Port`; added a deployed-row backfill by hand after review. Generation used throwaway system DB and configured history bind, not production data.
- Sensitive path review pending for cleanup/macro: no untrusted shell interpolation, no secret-bearing logs or responses, preserve fingerprint and Nagios validation. No VM tests performed yet.
- Resource macro design: `$USER1$` is left for the Nagios plugin directory (convention). `$USER2$..$USER256$` (255 slots) are managed by `resource_macros.py`. Slot assignment is stable per `(kind, id)` key — NCPA tokens keyed `"ncpa_token:{device_id}"`, custom-check passwords keyed `"custom_check:{config_id}:{field_name}"`. Substitution is post-generation string replacement in the check_command text — `resolve_plugin_command` is unchanged and still validates values (tokens/passwords cannot contain `!`, `$`, etc. by the existing validator). The `write_resource_block` call is skipped silently when resource.cfg does not exist, with a warning log; the macro references are still written to hosts.cfg so the config can be fixed without regenerating. On the lab appliance `resource.cfg` is `nagios:nagios` 0660 — the `pinpoint` user (group `nagios`) can write it. The `write_resource_block` function sets mode 0640 on the temp file before `os.replace`; `chown nagios:nagios` requires elevated privilege and is a responsibility of the installer (same pattern as the existing hosts.cfg ownership contract).
- `NAGIOS_RESOURCE_CFG` added to `config.py` (default `/usr/local/nagios/etc/resource.cfg`, overridable via env); needs to be added to the README production settings table and the PinPoint Installer contract in the same PR.

- 2026-10-14 audit supersedes round 9 completion claims: issue C8 requires resource mode 0660 and owner nagios:nagios to be preserved, not changed to 0640. Atomic replacement now copies existing uid/gid/mode; insufficient chown privileges abort before replacement. New files default to 0660, but production ownership and installer compatibility still need proof. Synthetic preservation regression failed before fix (416 vs 432), then passed. No lab changes made this session.
- Process-secrecy blocker: https://assets.nagios.com/downloads/nagioscore/docs/nagioscore/4/en/macros.html says macros expand before command execution. `plugin_registry.py` renders NCPA token with `-t '$ARG2$'`, so resource macros do not keep it out of argv. Asked the owner whether to extend credential transport or revise the issue; Owner chose "Preserve process secrecy; extend design" in this session; supported credential file/stdin inputs are authorized, with explicit blockers for plugins that lack them. Workflow §4 requires a person to resolve the specification conflict; sensitive-module authorization already persists and is not being requested again.
- Synthetic substitution reproducer: a dummy token `cpu` in `pinpoint_nd_ncpa!5693!cpu!cpu/percent` becomes `pinpoint_nd_ncpa!5693!$USER2$!$USER2$/percent`, corrupting the metric path. Replace secrets at their known argument positions rather than across whole commands. The custom password tests using invalid `Plugin_Variables` do not prove actual encrypted CUSTOM check rendering; retain real custom-check regressions and add effective-command equivalence tests.

- Owner decision received: retain process secrecy and extend the design using supported credential file/stdin inputs, explicitly blocking unsupported plugins. The implementation plan is `docs/plans/Issue_129_Check_Secret_Transport.md`. Current upstream NCPA client 1.2.5 has no secure token input; stock SMB 2.4.12 passes its password to smbclient argv. C plugins require installed `--extra-opts` verification. Read-only installed-plugin inspection via SSH failed with connection refused on configured loopback port 2250; no lab changes made.
- Resumed saved unit suite: 2638 passed, 14 skipped, 5 failed, 1 error; every failure was sandbox socket/DNS denial (socket PermissionError errno 1; example.com resolution errno -3). Stage run after writer fix: 2640 passed, 14 skipped, same 5 failures/1 error. Rerunning backend outside sandbox under approved escalation; do not weaken those tests.
