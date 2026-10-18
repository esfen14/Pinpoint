# Test run: issue #234 NCPA helper and metric attachment

| | |
|---|---|
| Date | 2026-10-19 Asia/Manila |
| Commit tested | App source `4aa4e1eb` (the three relevant deployed Python files matched byte-for-byte); working branch `issue-234-ncpa-helper` |
| Plan | Issue #234 acceptance criteria; normal NCPA deployment and Network Health observation |
| Tester / executor mode | Codex, scripted authenticated API and SSH diagnostics; no browser session |
| Catalog revision and SHA-256 | N/A (not a QA catalog run) |
| Queue / set / session / batch | N/A |
| Deployed application / installer revision | App files match source commit `4aa4e1eb`. VM base installer stamp `697869e`; installed helper bytes SHA-256 `92d3350b9e1029c801adcd99843859cc84f8a14264603ba2dcba5aac3a1424f3`, matching helper source at installer PR #7 commit `b166953d2e7e5b4bae12bf723712224cc97fae94`. |
| Baseline / preflight / restoration | `scripts/vmlab preflight` passed before deployment. Used demo target `web02` (`10.77.0.3`); deployment was intentionally retained for monitoring verification. No agent or resource cleanup performed. |
| Start / end / time zone | 2026-10-18 19:23–19:27 UTC (2026-10-19 Asia/Manila) |
| Environment | Installer-built QA VM, Ubuntu Server 22.04.5 lab image, Nagios Core 4.5.11, isolated lab `10.77.0.0/28`, upgraded application database |
| Raw evidence | Sanitized command/API observations are summarized below; no separate raw capture was retained. |

## Result

**Overall: Partial.** A normal deployment succeeded with the currently installed restricted helper and produced CPU, memory, and disk performance data in Network Health. The helper rejection from the user report did not reproduce on this QA VM; the issue body’s earlier diagnosis of a missing helper/sudo rule remains historical context for that earlier occurrence only. Failure-path and UI regression checks remain to be run.

Totals (unique TC): Pass 3, Fail 0, Partial 0, Blocked 0, Inconclusive 1, Not run 1.
Totals (unique E2E): Pass 1, Fail 0, Partial 0, Blocked 0, Inconclusive 0, Not run 0.
Historical credit: 0 accepted, 0 partial; historical issue context was not counted as a new execution.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| Helper deployment and authorization | Pass | `resource.cfg` was `nagios:nagios 0660`; helper was `root:root 0755`; sudoers parsed OK and granted only the helper with no arguments. An empty request was rejected with exit 1 as expected. Its generic fixed error did not expose request content. | |
| Normal NCPA wizard deployment | Pass | `scripts/vmlab ncpa 10.77.0.3`: host-key trust, login/sudo check and run all passed; run 2 ended `Success`, device outcome `Success`, device state `Deployed NCPA`. | |
| Network Health NCPA metrics | Pass | API service detail for `dev-c61190` showed CPU `Ok` with perfdata, memory `Warning` at 50.50% with perfdata (the configured warning threshold is 50%), and root disk `Ok` with perfdata. `/network-health/trends` returned non-empty CPU, memory and disk series (24 points each). The first API query filtered by display name `web02` and returned no rows because live hosts are named `dev-*`; the corrected IP-to-host mapping query passed. A first assertion also incorrectly required memory to be `Ok`; it was corrected to assert metric presence/perfdata, since Warning is a valid measured state. | |
| Reported helper rejection | Inconclusive | No rejection occurred during the current supported deployment. The VM contains the helper from installer PR #7 and exact sudo authorization. Earlier issue context identifies a previous setup where both were absent, but does not establish that this is the cause of the current user report. The helper itself reports only a generic rejection, so a fresh failing environment is required for exact diagnosis. | [#234](https://github.com/esfen14/Pinpoint/issues/234) |
| Agent success with attachment rejection | Not run | To be covered by isolated backend regression tests with a controlled helper/config rejection. | [#234](https://github.com/esfen14/Pinpoint/issues/234) |
| Failure-stage UI behavior | Not run | Browser UI was not exercised in this run. | [#234](https://github.com/esfen14/Pinpoint/issues/234) |

## Expected-item observations and restoration

| Case / attempt | Expected item | Observed value | Verdict | Private evidence reference | Restoration verified |
|---|---|---|---|---|---|
| Helper preflight | Fixed helper, exact authorization and protected metadata | `root:root 0755`; exact no-argument grant; `nagios:nagios 0660`; sudoers valid | Pass | Sanitized SSH diagnostic output; no raw file contents or credentials retained | N/A, read-only |
| Web02 deployment | Explicit overall and per-device success | Run 2 `Success`; device `Success`; NCPA state `Deployed NCPA` | Pass | `scripts/vmlab ncpa 10.77.0.3` output | Deployment intentionally remains installed for monitoring check |
| Network Health metrics | CPU, memory and disk checks with live performance data | All three service details returned perfdata; memory was legitimately Warning; all three Network Health trend arrays contained 24 points | Pass | Authenticated API observations | Deployment intentionally remains installed |
| Current helper rejection reproduction | Actionable sanitized failure evidence | Not reproduced; no failure to diagnose on this supported VM | Inconclusive | See observations above | No rejected write occurred |

## Deviations from the plan

- The existing QA VM already had the restricted helper, so the historical missing-helper failure could not be reproduced without changing the environment. No helper or sudoers mutation was made.
- The helper returns only one generic nonzero failure message; exact validation subreason is unavailable from this installed version.
- UI checks and the controlled attachment-failure test were deferred to the implementation/test round.

## Follow-up

- Defects found: issue #234 covers stage-aware installation/attachment results and the generic helper rejection message.
- Repeat the current-report rejection against the originating installer/application environment once its revision and sanitized helper diagnostics are available.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
