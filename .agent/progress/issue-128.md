# Issue #128: System Refinement Add Load Average, Swap and Disk I/O Defaults and Guided Process Check

Branch: `issue-128-ncpa-process-check`
Status: blocked

## Finish condition

Copied from issue sections E, F and H; tick only with observed evidence.

- [ ] E: New defaults become services and report OK on a lab NCPA host.
- [ ] E: Three existing metrics and service names unchanged.
- [ ] E: Unsupported agent paths are skipped instead of creating failing services.
- [ ] E: Documented process path accepted by settings validator.
- [ ] E: Guided process check produces a reviewable row and saves.
- [ ] E: Invalid process names blocked with a message.
- [ ] E: Existing table behavior/tests unchanged.
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

1. [ ] Obtain lab-agent access/approval and confirm valid NCPA paths, units and process-check syntax on NCPA 3.5.0; record lab evidence in `docs/test-runs/` (only after human direction).
2. [ ] Test-first backend defaults and unsupported-path skipping in `server/tests/test_plugin_registry.py` (locate actual test paths), then implement `server/config.py`, `server/app/network_discovery/plugin_registry.py` and any necessary host planning code; verify backend.
3. [ ] Test-first process-path validator in `server/tests/test_plugin_settings.py` (locate actual path), document pattern in `docs/manuals/Custom_Checks_Manual.md`; verify backend/docs.
4. [ ] Test-first guided process add, invalid name, row review/save in `client/src/test/PluginSettings.test.tsx`; implement in `client/src/components/settings/PluginSettings.tsx` and types/API only if necessary; verify frontend.
5. [ ] Run required regressions including `test_ncpa.py`; confirm two lab targets OK, absent path skipped, Nagios load and per-device service count, recording evidence in `docs/test-runs/`; review sensitive-module injection and secrets.
6. [ ] Update `spec files/Data_Model_and_Integrations.md`, `spec files/Frontend_Modules_and_Routes.md`, `spec files/Implementation_Status.md` and user-facing help/manual as needed; verify docs.
7. [ ] Re-read issue, prove all applicable finish items, run `scripts/verify.sh all`, attach output, remove progress and open PR using template; seek CI/reviewer approvals (do not claim approval or merge).

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| resumed | Checked issue and branch after Docker lab approval; inspected lab instructions | `docker info --format '{{.ServerVersion}}'` | Cannot run: `/bin/bash: line 1: docker: command not found` |
| resumed | Re-ran last check; Docker CLI is now available but daemon access denied; issue has no new comment addressing blocker | `docker info --format '{{.ServerVersion}}'` | `permission denied while trying to connect to the docker API at unix:///var/run/docker.sock` |

## State for the next session

- Last check run (exact command): `docker info --format '{{.ServerVersion}}'`
- Result (first failing lines, or "green"): `permission denied while trying to connect to the docker API at unix:///var/run/docker.sock` (exit 1).
- Hypothesis: Docker CLI is now present but this user cannot access the daemon, so the approved lab cannot be started here.
- Next action (one specific step, not "continue"): Grant this environment Docker daemon access for the approved lab with two NCPA 3.5.0 targets, or supply sanitized probe results (paths, units, process queryargs) and two-target Nagios verification evidence.

## Decisions and notes

- Issue's finish condition covers the stated requirements by E, F and H; database migrations are explicitly N/A; new endpoints are only applicable if implementation needs them.
- `spec files/Engineering_Standards.md` marks `app/network_discovery/` sensitive. Before changing it, review injection, secrets and Nagios pre-apply validation.
- User approved Docker lab usage; Git author identity has been configured and the plan was committed/pushed in df6e4afc. Initially this environment had no Docker executable; on resume the CLI exists but Docker daemon access is denied. `docs/manuals/Local_Lab.md` also notes the Docker targets cannot test NCPA installation because they lack init; a suitable two-agent lab is still needed. No agent probes or lab claims have been made.
