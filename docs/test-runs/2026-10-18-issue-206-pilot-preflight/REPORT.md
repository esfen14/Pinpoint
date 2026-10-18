# Appliance preparation: TC-SS-04 pilot

| Field | Observation |
|---|---|
| Date / executor | 2026-10-18; Codex scripted SSH/API preparation; Paeng authorized exclusive appliance access, deployment and disposable Staff setup |
| Case execution | None; no acceptance attempt or batch opened |
| Catalog SHA-256 | `d9374c41d7f4e5304c3475735d765ad66cb4352cc9745f76e96d78c4de0e398f` |
| Queue / set / owner | [v3 JSON](../../qa/queues/2026-10-18-today-ss04-v3.json), `today-ss04`, Paeng; execution card still empty/BLOCKED |
| Preparation checkout | `04f317e9063fac64ac995824e997685f99f8887f` before these report changes |
| Application revision | Before: `82ba9ce9aefda8fbbad93ba500a9cacf23c56409`; deployed: `299ab3ba7203c89a3ca5d8fabea42d9e5f239be2` |
| Installer revision | Unknown; existing installation retained; no installer run or snapshot restore |
| Appliance | `pinpoint-qa-appliance`, UUID `351eb491-f5e1-4854-a7e4-68309ad774ad`; exclusive local VirtualBox; Ubuntu 22.04, Nagios Core 4.5.11 |
| Runtime / build | Python 3.14.8, Gunicorn 26.2.0; Node 22.23.3 / npm 10.9.9; frontend built from the exact target and committed lockfile |
| Time / baseline | Preparation window 06:34–06:54 UTC (14:34–14:54 Asia/Manila); VM boot around 06:34 UTC; app restarted 06:48:15 UTC; post-deploy observation 06:50:11 UTC (UTC+8 local); existing upgraded databases |
| Raw evidence | Private host directory `/home/paeng/pinpoint-test-results/2026-10-18-issue-206-preparation`; mode 0700 directories / 0600 files; never committed |

## Result

**Preparation completed; acceptance Not run.** The target is deployed and the
Staff prerequisite is initialized. Production driver integration, a complete
execution card, fresh runtime proof and an explicit test start remain pending
under [#206](https://github.com/esfen14/Pinpoint/issues/206). These setup observations
are not a TC-SS-04 PASS or a supervisor proof receipt.

Totals (unique TC): Pass 0, Fail 0, Partial 0, Blocked 0, Inconclusive 0, Not run 1.
Totals (unique E2E): Pass 0, Fail 0, Partial 0, Blocked 0, Inconclusive 0, Not run 0.
Historical credit: 0 accepted, 0 partial. Setup operations are not test attempts.

| Case | Result | Observation | Follow-up |
|---|---|---|---|
| TC-SS-04 | Not run | Staff setup verified; no browser login, sidebar inspection or `/system-status` navigation performed | [#206](https://github.com/esfen14/Pinpoint/issues/206) |

## Preparation observations

- Held the cooperative host claim during VM operations and guest probes. UUID,
  controller PID 117877/start ticks 1811322, VM PID 118118/start ticks 1811866 and
  unique loopback forwards agreed before/after. The powered-off existing VM was
  started; no other VM or target was started or reset.
- Initial inspection found the old application revision and no Staff users.
  The saved credentials alone did not prove a usable account or current deployment.
- Stopped Gunicorn for a consistent backup before changing application files,
  dependencies or databases. Backed up the full existing application, virtual
  environment, application/Nginx/Nagios configuration and service unit, plus SQLite
  backup copies. Compression, archive inventory and database quick checks passed.
- Backup: guest `/var/backups/pinpoint/qa-20261018-299ab3b`; an independent host
  copy is `appliance-before.tar.gz` in the private evidence directory. Archive is
  184686734 bytes; SHA-256
  `546b71c3db2a4eec4e516515b1ed7073a753a5799145699fdd74d4cc2b9e9a0d`.
  This is verified backup creation, not a restore rehearsal.
- Transferred an immutable Git bundle for the exact target, built its frontend
  in a staging checkout with `npm ci` and `npm run build`, deployed the exact Git
  revision, installed runtime requirements, passed dependency checks, applied
  committed multi-database migrations and started Gunicorn. No product source was
  edited. The build reported the existing large-chunk warning.
- Both database revisions advanced from `b7d3f1a9c264` to `e153c4a8b2d7`;
  both post-upgrade quick checks returned `ok`. Existing administrator identity,
  role, status and setup flags were retained; one Staff user was added. Five
  discovery devices and three discovery-status records were unchanged between
  the consistent backup and final inspection. This does not assert byte-identical
  databases: migrations, setup and audit records intentionally changed them.
- Deployed `server/app` (123 tracked files) and `client/src` (279 tracked files)
  matched their target Git blobs, with zero tracked application changes. The
  controlled service start followed deployment; observed master PID 3059/start
  ticks 83035 and worker PID 3060/start ticks 83048 use the deployed server directory.
  No in-memory import attestation or production-supervisor proof was fabricated.
- `/login` returned 200. All 16 served frontend artifacts matched the exact staged
  build and deployed disk hashes. The new index SHA-256 is
  `fe7059b909cff6904a09c417c530ce6eded4b39d6ef10655a09e7c0ed5155bf5`.
  Nginx and Nagios remained active; the application is active.
- Created the disposable Staff user through supported account APIs, completed its
  forced password change, and verified Active status, active Staff role, zero
  permissions, `needs_setup=false` and `must_change_password=false`. Credentials
  remain in private host state; neither passwords nor cookies enter this report.
  Staff and administrator setup sessions were logged out and `/api/user/me`
  returned 401 for each.
- The reviewed runner image is available locally:
  `sha256:e37b02e1817b35e6a0953bdfed1e4a285cc9f3d1d86ac77c1d2fedef0da6c7a5`.
  No container or browser was launched by this preparation; availability is not
  proof of a successful browser run.

## Deviations and corrections

The existing scheduler launched discovery automatically after VM boot, from
06:39:54.579300 to 06:40:05.828340 UTC, before the application was paused. Its record
reports SUCCESS; the configured scope read back as `10.77.0.0/28`. No agent/API
scan command was issued. This was outside the intended scan-free preparation and
is disclosed rather than counted as case evidence. The pre-update backup was
created after this scan. Final inspection found no nmap process; scan-record counts
stayed at three after the backup. A pre-boot baseline is not claimed.

The scheduler is now off through a temporary service environment override:
`/run/systemd/system/pinpoint-gunicorn.service.d/90-qa-preparation.conf` loads
`/run/pinpoint-qa-preparation.env` with `PINPOINT_SCHEDULER=0`. Persisted application
configuration and service unit match the backup. This also pauses polling and
scheduled maintenance; the baseline is suitable for permission-pilot preparation,
not timing, monitoring, discovery or remediation acceptance. Reboot removes this
runtime override: stop and recheck the baseline before further preparation. Do not
re-enable the scheduler or reboot as an unreviewed recovery step.

Preparation script corrections, all before acceptance:

- The system Python lacked `hashlib.file_digest`; backup finalization resumed
  against the existing archive, verified it and wrote its manifest.
- A restrictive staging-parent mode prevented `npm ci`; corrected traversal
  permissions and reran the build without changing the committed lockfile.
- The first login with the configured controller's stale administrator identity
  returned 401. Compared identity fingerprints privately, used the saved matching
  administrator credentials, and succeeded; no administrator reset occurred.
- The initial deployed static files had private modes, causing `/login` HTTP 500;
  corrected only public frontend file/directory modes. The final 200 and 16 exact
  artifact matches supersede that setup failure; no case verdict was recorded.

## Expected-item observations and cleanup

| Case / attempt | Expected item | Observation | Verdict | Private evidence | Cleanup |
|---|---|---|---|---|---|
| TC-SS-04 / 0 | E1 | Sidebar visibility and redirected page not observed | Not run | No acceptance artifacts | Setup sessions closed; no acceptance resources created |

Private evidence includes `preflight-before/summary.json`,
`preflight-after/summary.json`, `maintenance/staff-preparation.json`, maintenance
outputs/manifests and `appliance-before.tar.gz`. The VM is left running on the
new target with its scheduler disabled. No fault injection, snapshot restore,
installer update or test-case execution occurred.

## Follow-up

1. Integrate the trusted pilot driver with fresh actual deployment/baseline proof,
   bounded bridge/container lifecycle, result parsing and verified session cleanup.
2. Complete/review the TC-SS-04 execution card using this baseline, private evidence
   paths and pinned image. Preserve the fixed one-case scope and original human results.
3. Show the executable scope and obtain a separate explicit start before launching
   acceptance. Do not copy transport previews or use a host browser to bypass gates.
4. Restore ordinary scheduler operation only in separately reviewed scope; keep
   backup restoration separate from routine test cleanup.

## Documentation verification

`scripts/verify.sh docs` passed (165 isolated contracts); the unchanged v3
queue source check, progress structure and whitespace checks passed. No local
backend test suite or unchanged frontend suite was rerun. The target frontend
build and runtime dependency checks were deployment validation, not acceptance.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No target addresses outside the documented lab range; host loopback is transport only
- [x] Raw evidence remains private; only sanitized observations and hashes are committed
