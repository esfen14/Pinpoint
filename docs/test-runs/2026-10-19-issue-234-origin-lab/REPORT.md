# Test run: issue #234 originating appliance diagnostics

| | |
|---|---|
| Date | 2026-10-19 Asia/Manila |
| Commit tested | Deployed app `65a5862c375dd7dfe1dd98433ca017dc4efe0cec`; current investigation branch code was not deployed to this appliance |
| Plan | Confirm the reported helper failure on the originating disposable appliance using read-only diagnostics |
| Tester / executor mode | Codex, SSH read-only diagnostics; no browser session or deployment mutation |
| Catalog revision and SHA-256 | N/A (issue investigation, not a catalog run) |
| Queue / set / session / batch | N/A |
| Deployed application / installer revision | App source commit `65a5862c`. Installed helper SHA-256 `92d3350b9e1029c801adcd99843859cc84f8a14264603ba2dcba5aac3a1424f3`, matching installer PR #7 helper source commit `b166953d2e7e5b4bae12bf723712224cc97fae94`. No `/etc/pinpoint-vmlab-stamp` was present, so the appliance's base installer revision could not be identified. |
| Baseline / preflight / restoration | Existing SSH host key was already in the workstation's known-hosts file. Only metadata, service identity, sudo authorization and filtered journal timestamps were read. An empty helper request returned its expected rejection code; `resource.cfg` SHA-256 was unchanged. No config, service, agent or account was changed. |
| Start / end / time zone | 2026-10-19 04:43–04:48 Asia/Manila (2026-10-18 20:43–20:48 appliance local time) |
| Environment | Originating disposable PinPoint appliance, Ubuntu Server 22.04.5. Nagios version and database state were not queried. No network scan was run. |
| Raw evidence | No raw logs retained. Sanitized observations came from the appliance system journal and file metadata; no command output containing credentials or resource values was copied. |

## Result

**Overall: Partial.** The originating appliance's journal confirms the reported helper rejection at 2026-10-18 18:21:05 UTC on app commit `65a5862c`. The current helper and its dedicated sudoers drop-in were created at 18:33:01 UTC, after the failure, and now have the expected hash, ownership, mode and exact no-argument authorization. This confirms the helper setup had not converged when the reported failure occurred; the older application retained only a generic nonzero-helper message, so the exact low-level rejection reason is unavailable. The base installer revision is also not stamped on this appliance.

Totals (unique TC): Pass 0, Fail 0, Partial 0, Blocked 0, Inconclusive 0, Not run 0.
Totals (unique E2E): Pass 0, Fail 0, Partial 0, Blocked 0, Inconclusive 0, Not run 0.
Historical credit: 0 accepted, 0 partial; this is an issue-specific diagnostic run, not a catalog execution.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| Reported rejection and deployment revision | Partial | Filtered system journal shows the helper rejection at 18:21:05 UTC. Deployed app checkout is `65a5862c`. The application logs a generic rejection for every nonzero helper exit and did not retain helper output, so it cannot distinguish missing sudo authorization from a helper-side validation rejection. | [#234](https://github.com/esfen14/Pinpoint/issues/234) |
| Helper setup chronology | Pass | Current helper and `/etc/sudoers.d/pinpoint-apply-resources` both have filesystem birth time 18:33:01 UTC, after the failure. Current helper hash matches installer PR #7 commit `b166953d`; the separate base installer stamp is absent. | [#234](https://github.com/esfen14/Pinpoint/issues/234) |
| Current protected-helper readiness | Pass | Helper is `root:root 0755`; resource file is `nagios:nagios 0660`; the app service runs as `pinpoint`; `sudo -l -U pinpoint` lists only the helper with no arguments for this grant. An empty request exits 1 and the resource-file hash is unchanged. | |
| Live NCPA deployment and metrics on this appliance | Not run | This visit was limited to diagnostics. A separate recorded live run on the supported QA VM deployed NCPA and observed CPU, memory and disk perfdata in Network Health; see [the first issue #234 report](../2026-10-19-issue-234-ncpa-helper/REPORT.md). | |

## Expected-item observations and restoration

| Case / attempt | Expected item | Observed value | Verdict | Private evidence reference | Restoration verified |
|---|---|---|---|---|---|
| Filtered app journal | Historical helper failure timestamp | 2026-10-18 18:21:05 UTC | Partial | Sanitized journal query; no raw capture retained | N/A, read-only |
| Helper installation | Fixed executable and revision | `root:root 0755`; SHA-256 matches helper at PR #7 commit `b166953d`; birth 18:33:01 UTC | Pass | Sanitized `stat` and `sha256sum` observations | N/A, read-only |
| Helper sudo grant | Exact service-user authorization | Current sudo listing for `pinpoint`: `(root) NOPASSWD` helper with empty argument list; drop-in birth 18:33:01 UTC | Pass | Sanitized `sudo -l` and `stat` observations | N/A, read-only |
| Empty helper request | Rejected safely without changing resources | Exit 1; resource-file hash unchanged | Pass | Sanitized exit/hash comparison | Yes |

## Deviations from the plan

- No new NCPA deployment or UI walkthrough was run on this appliance; target-device credentials and an app UI session were not supplied. Existing live deployment and metric evidence remains in the separate report.
- No helper stdout/stderr was recovered. The deployed app intentionally suppressed that output, and the system journal retained only the generic application error.
- The appliance has no installer base stamp. The installed helper's bytes identify its source revision, but not the complete ISO/installer revision.

## Follow-up

- Defects found: [issue #234](https://github.com/esfen14/Pinpoint/issues/234).
- Keep the issue open until a supported installer build records its revision and the complete acceptance run is verified on the updated app; the original low-level helper rejection detail is not recoverable from this appliance's existing logs.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No private lab addresses
- [x] Evidence is referenced by type and location, not pasted
