# Test run: issue-129 credential transport

| | |
|---|---|
| Date | 2026-10-14 |
| Commit tested | Application `7f531562`; installer `faca298`; pushed PR checks `d536fdfc` |
| Plan | [Check secret transport](../../plans/Issue_129_Check_Secret_Transport.md) |
| Tester | Codex |
| Environment | Host isolated test suite; existing Ubuntu 22.04.5 QA appliance, installed NCPA client 1.2.4 and Nagios Plugins 2.4.12. Application source was not synced or deployed. No database migration or managed config replacement. |
| Raw evidence | Local git-ignored `test-results/issue-129/`: `secure-transport-backend.log`, `secure-transport-frontend.log`, `transport-compatibility-observations.txt`. Earlier NCPA-only stage: `secure-ncpa-backend.log`. |

## Result

**Overall: Partial.** Supported check adapters pass automated process-secrecy and regression checks. The installer helper is a local implementation with isolated tests, still requiring application invocation and installed service-user acceptance. No full Nagios-engine or live monitoring parity is claimed.

Totals: Pass 7, Fail 0, Blocked 2, Skipped 1.

## Cases

| Case | Result | Notes | Issue |
|---|---|---|---|
| Backend regression | Pass | `scripts/verify.sh backend`: 2756 passed, 14 existing skips. Focused transport/config target: 278 passed. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Frontend regression | Pass | 42 files/554 tests passed; build passed; lint 0 errors/29 warnings. Docs verification also passed. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Running NCPA argv | Pass | A persistent fake plugin receives its protected token in memory; Linux process argv contains no synthetic token and the adapter has no child. Safe errors and credential-bearing output suppression tested. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Running native parent/child argv | Pass | A persistent executable verifies its password on extra-options stdin. Both parent and child process arguments exclude the synthetic password. Unsupported capability/SMB and unsafe inputs refused. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Actual installed NCPA client parity | Pass | Read-only copy of installed client 1.2.4 executed locally with mocked HTTP transport. Success/critical output, performance data and exit codes match its original options; authentication/connection errors remain safe UNKNOWN. No real network request. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Installed native stdin capability | Pass | Installed check_nt 2.4.12 accepted a synthetic password through stdin against a temporary loopback responder; expected uptime/performance result and no-password argv observed. No managed config or remote target changed. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Installer helper isolated contract | Pass | Five standard-library tests: metadata/outside preservation, rollback, path/digest rejection, invalid blocks/slots/permissions, atomic failure cleanup. Installer shell syntax/diff checks pass. Helper not installed. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Application helper invocation and installed ownership/rollback | Blocked | Application resource writer does not yet invoke installer helper. Isolated ownership tests do not prove installed service-user compatibility. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Full live Nagios parity/process/permissions | Blocked | New build has not been deployed to Nagios. Runtime engine macro handling, installed readability, successful live checks and native Radius/MySQL parity remain unverified. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Remaining upgrade/cleanup/acceptance journeys | Skipped | This round covered credential transport; other live issue acceptance cases were not repeated. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |

## Deviations from the plan

The secure adapter uses bare USERn identifiers rather than dollar-delimited macro arguments, so Nagios cannot expand the token before execution. NCPA client options are supplied in memory in the same process; native plugins receive INI options on stdin. Password-bearing SMB generation refuses explicitly; it is never silently removed, paused or passed insecurely. These are the owner's authorized extensions to preserve process secrecy.

The prior failing process diagnostic remains valid for the prior macro-only implementation; this report records a new run rather than changing that historical result. Current source assertions recover credentials from the same owned slots and retain public fields, output and performance data rather than demanding insecure expanded argv equivalence.

## Follow-up

- Wire the restricted helper protocol into resource updates and rollback, then verify as the actual application service user.
- Run the remaining authorized live Nagios and issue acceptance cases before ticking macro/final completion.
- All three CI checks passed for pushed `d536fdfc`; application `7f531562` and installer `faca298` remain local and have not run remote CI.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
