# Test run: issue-129 helper integration

| | |
|---|---|
| Date | 2026-10-14 |
| Commit tested | Application `ea0a4284`; installer functional source `15c27d1` (documentation follows in `b166953`); remote adapter CI `d1d60627` |
| Plan | [Check secret transport](../../plans/Issue_129_Check_Secret_Transport.md) |
| Tester | Codex |
| Environment | Host isolated suites; existing Ubuntu 22.04.5 QA appliance, Nagios 4.5.11, NCPA client 1.2.4; existing web01 target started headlessly, guarded network 10.77.0.0/28. Database read-only; full application source/database not upgraded. |
| Raw evidence | Local git-ignored `test-results/issue-129/`: `helper-integration-verify-all.log`, `helper-checkpoint-focused.log`, `installed-helper-acceptance.log`, `live-ncpa-adapter-parity.log`. |

## Result

**Overall: Partial.** The application uses the restricted helper for foreign-owned default-path resources and exact rollback. Installed service-user ownership/privilege tests and four real NCPA adapter comparisons pass. The complete generated configuration has not been applied/reloaded under the main Nagios service, so macro/final completion remains open.

Totals: Pass 6, Fail 0, Blocked 2, Skipped 1.

## Cases

| Case | Result | Notes | Issue |
|---|---|---|---|
| Full verification | Pass | All gate: 2766 backend passed/14 existing skips, 42 frontend files/554 tests passed, build passed, lint 0 errors/29 warnings, docs passed. Ran on helper integration worktree before doc-only updates. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Committed helper/config source | Pass | Focused helper/resource/config suite on ea0a4284: 113 passed, including 10 new stdin protocol, failure and rollback cases. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Installer security boundaries | Pass | Seven stdlib tests; new external-slot whitespace and missing block/footer separator regressions failed before fixes and passed afterward. Shell syntax/diff checks pass. Installed executable source digest matched local 15c27d1. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Actual service-user resources | Pass | New resource client executed as pinpoint against installed helper. Synthetic owned block write retained outside bytes, nagios:nagios 0660; actual Nagios validation passed; original bytes/metadata restored after normal and rejected/cancelled transactions. Client import used a standalone registry validation constant; all filesystem and sudo calls were real. No Flask request/scheduler path driven. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Installed privilege restrictions | Pass | Helper root:root 0755, interpreter target root:root 0755, sudoers root:root 0440. Exact no-argument grant accepted normal request; wrong destination, command argument and arbitrary cat privilege probes refused. Only helper/grant installed. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Live NCPA adapter parity/argv | Pass | Current host config has no NCPA service objects. Read stored deployed web01 token/partition metadata without logging or writing credentials. Four direct CPU/virtual/swap/disk checks were OK with stock client and protected adapter as nagios, preserving performance series. Inspected adapter processes/descendants: token absent from argv. Original resource bytes/metadata restored. Baseline token was supplied only in Python memory. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Full generated-config main-daemon acceptance | Blocked | Current full application/config has not been upgraded, generated, applied or reloaded in the main Nagios service. Existing live hosts mode remains 0664; source applies 0640 but that installed apply/readability case remains unverified. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Paired remote CI/review | Blocked | New helper integration and installer changes remain local pending owner push approval. Application d1d60627 CI is green; installer origin denies this account push access. Publishing a fork/draft PR needs the owner's choice. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Complete ISO/upgrade/cleanup journeys | Skipped | Seven helper tests and installer packaging syntax do not prove an ISO build or full upgrade. Other issue live journeys were not repeated. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |

## Deviations from the plan

Initial NCPA preflight found no matching service objects and all targets stopped. Started only existing web01 (512 MiB, over 6 GiB host available RAM), using existing deployment/partition metadata for direct live comparisons. No new device deployment, target reprovision, snapshot reset, discovery, database migration or main Nagios reload occurred. This is live adapter evidence, not full generated-config/engine acceptance.

The helper was installed separately with its exact privilege rule; the broad installer privilege script was not rerun. Owned resource changes were temporary and restored byte-for-byte. Temporary acceptance scripts/bytecode were removed; the helper/sudo grant remain installed. QA appliance and web01 remain running, other targets stopped.

## Follow-up

- Run the paired application/installer upgrade and complete generated-config validation, apply/reload, readability, main engine result/process and snapshot/log cases.
- Keep the explicit password-bearing SMB refusal; its plugin lacks secure child credential input.
- Ask before pushing application checkpoints. Installer origin lacks write permission: share the local branch/patch or publish through an approved fork/draft PR.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
