# Issue #128: System Refinement Add Load Average, Swap and Disk I/O Defaults and Guided Process Check

Branch: `issue-128-ncpa-process-check`
Status: in-progress

## Finish condition

Copied from issue sections E, F and H; tick only with observed evidence.

- [x] E: New defaults become services and report OK on a lab NCPA host.
- [x] E: Three existing metrics and service names unchanged.
- [x] E: Unsupported agent paths are skipped instead of creating failing services.
- [x] E: Documented process path accepted by settings validator.
- [x] E: Guided process check produces a reviewable row and saves.
- [x] E: Invalid process names blocked with a message.
- [x] E: Existing table behavior/tests unchanged.
- [ ] F: Updated application source; API endpoints (if needed) with docstrings and permissions; migrations N/A; frontend components/types/routes as applicable; unit, frontend and integration/regression tests; technical and user documentation/help; attached `scripts/verify.sh all` output.
- [ ] H: Functional completion, edge cases, unchanged behavior; code quality, conventions, lint and static checks; automated/integration/regression evidence; input validation, authorization, secrecy, error handling, performance; technical/user/config/deployment documentation; PR references issue with testing and CI evidence, approvals and blocking comments resolved before merge.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Probe lab NCPA 3.5.0 for load, swap and disk I/O paths/units; record in PR | E defaults OK; F evidence; H testing | Lab probe transcript and PR evidence |
| Add confirmed defaults with sensible thresholds; names valid; preserve three existing entries | E defaults OK; E existing metrics; H unchanged behavior | `test_plugin_registry.py`, lab run |
| Unsupported path yields SkippedService reason, no CRITICAL storm | E skipped; H reliability | `test_plugin_registry.py` and lab unsupported-path probe |
| Process path/queryargs manual pattern; validator test | E validator; F user docs, unit tests | `test_plugin_settings.py`, manual |
| Guided process name/count action auto-fills metric/path/queryargs; review row and save | E guided row; F frontend; H functionality | `PluginSettings.test.tsx` |
| Invalid names blocked, keep existing validation | E invalid name; E existing behavior | `PluginSettings.test.tsx` |
| New service count/device and lab Nagios load | E defaults OK; H performance | Lab checks and PR description |
| No new endpoint/migration unless required; permissions, secure config, pre-apply validation | F API endpoints/migrations N/A; H security | Source review and regression tests |
| Existing default output unchanged where not explicitly changed | E existing metrics; H unchanged behavior | Existing and new registry regression tests |
| Sensitive module injection/secret review; avoid network calls without timeouts and unbounded work | H security/reliability | Source review and tests |
| User-facing states, labels, help; technical docs and Implementation Status | F docs; H documentation | UI tests, docs verification |
| Tests in G: two NCPA targets, `test_plugin_registry.py`, `test_plugin_settings.py`, `test_ncpa.py`, frontend test | E defaults; F tests; H testing | Real output attached to PR and `scripts/verify.sh all` |
| No completion before review approvals, CI and deployment evidence | H PR review | PR checks, approvals, lab records |

## Plan

1. [x] Obtain lab-agent access/approval and confirm valid NCPA paths, units and process-check syntax on NCPA 3.5.0; record lab evidence in `docs/test-runs/` (only after human direction).
2. [ ] Test-first backend defaults and unsupported-path skipping in `server/tests/unit/test_plugin_registry.py`, then implement `server/config.py`, `server/app/network_discovery/plugin_registry.py` and any necessary host planning code; verify backend.
3. [x] Test-first process-path validator in `server/tests/unit/test_plugin_settings.py`, document pattern in `docs/manuals/Custom_Checks_Manual.md`; verify backend/docs.
4. [x] Test-first guided process add, invalid name, row review/save in `client/src/test/PluginSettings.test.tsx`; implement in `client/src/components/settings/PluginSettings.tsx` and types/API only if necessary; verify frontend.
5. [ ] Run required regressions including `test_ncpa.py`; confirm two lab targets OK, absent path skipped, Nagios load and per-device service count, recording evidence in `docs/test-runs/`; review sensitive-module injection and secrets.
6. [x] Update `spec files/Data_Model_and_Integrations.md`, `spec files/Frontend_Modules_and_Routes.md`, `spec files/Implementation_Status.md` and user-facing help/manual as needed; verify docs.
7. [ ] Re-read issue, prove all applicable finish items, run `scripts/verify.sh all`, attach output, remove progress and open PR using template; seek CI/reviewer approvals (do not claim approval or merge).

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| resumed | Checked issue and branch after Docker lab approval; inspected lab instructions | `docker info --format '{{.ServerVersion}}'` | Cannot run: `/bin/bash: line 1: docker: command not found` |
| resumed | Re-ran last check; Docker CLI is now available but daemon access denied; issue has no new comment addressing blocker | `docker info --format '{{.ServerVersion}}'` | `permission denied while trying to connect to the docker API at unix:///var/run/docker.sock` |
| resumed | Re-read issue #128 and progress; no new comments resolving lab access; re-ran last check | `docker info --format '{{.ServerVersion}}'` | `permission denied while trying to connect to the docker API at unix:///var/run/docker.sock` (exit 1); remains blocked |
| resumed | User requested retry; refreshed group context reaches Docker daemon | `sg docker -c "docker info --format '{{.ServerVersion}}'"` | green: Docker 29.9.0 |
| 1 | Probed official NCPA 3.5.0 on two network-disabled containers; documented supported paths and absent load nodes | Direct authenticated API probes; `scripts/verify.sh docs` | Probe passed for swap, disk counters and exact process count; load not available; docs check below |
| 2 | Added confirmed defaults, cached bounded path probe, per-metric skipped reasons, guided process form and owning docs; unit HTTP probes mocked | Backend focused/regressions; process API; `scripts/verify.sh frontend`; `scripts/verify.sh docs`; backend stage running | 257 backend regressions and 58 settings tests pass; 34 targeted/567 full frontend tests pass; build/lint green (warnings); docs green; backend stage pending |
| 3 | Full backend stage exposed loss of established NCPA services on failed inventory; Docker default services independently reached OK on both targets | `scripts/verify.sh backend`; live status.dat inspection | 2585 passed, 14 skipped, 3 upgrade-rehearsal failures: expected CPU/memory services absent, expected 15 attached got 13, check_ncpa Enabled instead of Active; live 12/12 defaults OK |
| 4 | Distinguished unknown inventory from confirmed missing paths; kept established checks while deferring added defaults; mocked new network prerequisite in upgrade rehearsal | Continuity red/green; upgrade rehearsal + domain regressions; docs; live default/process/missing-path runs | 339 targeted tests pass; two targets default 6 services each OK, process checks OK, missing path omitted and skipped reasons persisted; full all pending |

## State for the next session

- Last check run (exact command): `cd server && FLASK_DEBUG=1 .venv/bin/python -m pytest tests/unit/test_upgrade_rehearsal.py tests/unit/test_plugin_registry.py tests/unit/test_create_host_cfg.py tests/unit/test_plugin_reconcile.py tests/unit/test_plugin_services_api.py tests/unit/test_plugin_settings.py tests/unit/test_ncpa.py -q > ../test-results/issue-128/backend-continuity-regression.log 2>&1`
- Result (first failing lines, or "green"): green: 339 passed in 31.53s. Docs green. Live defaults/process/missing-path checks green; resource sample finishing.
- Hypothesis: Upgrade regression resolved; final full verification should now pass.
- Next action (one specific step, not "continue"): Run `scripts/verify.sh all` once and attach its observed output to the PR, with completed live report and current source SHA.

## Decisions and notes

- Issue's finish condition covers the stated requirements by E, F and H; database migrations are explicitly N/A; new endpoints are only applicable if implementation needs them.
- `spec files/Engineering_Standards.md` marks `app/network_discovery/` sensitive. Before changing it, review injection, secrets and Nagios pre-apply validation.
- User approved Docker lab usage; Git author identity has been configured and the plan was committed/pushed in df6e4afc. Initially this environment had no Docker executable; on resume the CLI exists but Docker daemon access is denied. `docs/manuals/Local_Lab.md` also notes the Docker targets cannot test NCPA installation because they lack init; a suitable two-agent lab is still needed. This historical blocker was resolved; observed agent and Nagios evidence is recorded in the subsequent rounds.

- Docker access blocker resolved on user retry via `sg docker`; existing Docker lab authorization remains applicable.

- Confirmed API paths justify swap and sda read/write defaults; no load-average path exists on the probed version, so omit it per issue C.2. Disk device paths are editable and skipped where absent.

- Sensitive-module review: fixed IP-only HTTPS inventory URL, query parameters instead of shell execution, no redirects, bounded time/body/traversal/cache, sanitized failure reasons; no agent values or token in logs/response. Existing command validation and shared Nagios pre-apply/rollback writer retained.
