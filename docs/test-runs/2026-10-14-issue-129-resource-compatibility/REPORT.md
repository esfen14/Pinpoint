# Test run: issue-129-resource-compatibility

| | |
|---|---|
| Date | 2026-10-14 |
| Commit tested | `87e00907` full verification; `61ebb946` command-equivalence tests (application source unchanged) |
| Plan | [Issue #129 transport plan](../../plans/Issue_129_Check_Secret_Transport.md) |
| Tester | Codex; owner authorized sensitive application work and VM usage |
| Environment | Local isolated Python/React tests; existing Ubuntu 22.04.5 LTS QA appliance; NCPA check client 1.2.4; Nagios Plugins 2.4.12; documented VM lab 10.77.0.0/28; no database migration or app sync |
| Raw evidence | Local workstation: git-ignored `test-results/issue-129/verify-all.log`, `command-equivalence.log`, `installed-compatibility.txt` |

## Result

**Overall: Partial.** Config safety fixes and local verification pass. Installed
ownership preservation and secure plugin credential inputs block issue #129
completion. No process-secrecy or live monitoring-result pass is claimed.

Totals: Pass 6, Fail 0, Blocked 2, Skipped 4.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| Full local verification | Pass | `scripts/verify.sh all`: 2674 backend passed / 14 skipped; 554 frontend passed; build succeeded; lint 0 errors / 29 warnings. `verify-all.log`. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Secret-field substitution | Pass | Six reproduced corruptions corrected: matching public metric, port, username/query and overlapping values stay unchanged. `TestSecretArgumentSubstitution`. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Persistent slots and real device removal | Pass | File-roundtrip assignments retained; external slots excluded; removed generated device and last secret reclaimed; unsafe mode/malformed block/collision/write failure rejected. `TestPersistentSlots`, `TestMacroGenerationFailure`, actual generated-host removal test. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Config transactions across all writers | Pass | Mocked generation, validation, apply, exception and cancellation failures restore resources; resource-only changes apply; actual apply helper restores both files before second reload and sets live hosts mode 0640. `TestResourceConfigTransaction` and discovery/NCPA parametrized cases. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Effective command equivalence | Pass | On `61ebb946`, two strengthened tests confirm actual rendered encrypted-password service and NCPA CPU/memory command expansion equals the expected original commands. `command-equivalence.log`. This is config equivalence, not live result parity. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Installed compatibility inspection | Pass | Installed NCPA 1.2.4 has no token-file/stdin input; check_nt/mysql_query advertise extra-opts; SMB lacks it; radius absent; existing resource is nagios:nagios 0660. Help/version and stat were observed. `installed-compatibility.txt`. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Atomic resource ownership as service user | Blocked | An empty private sibling could be created, but fchown to the resource's existing nagios owner was denied as pinpoint. Probe file removed; live resource unchanged. A scoped installer update mechanism is required. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Process-list secrecy | Blocked | Macros expand into arguments; secure transport/adapter is unimplemented. Installed NCPA/SMB inputs need extension. Extra-opts advertised by C plugins has not been run with credentials. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Non-default listener deploy/probe/relocation | Skipped | No target deployment or relocation executed; app branch not installed on this guest. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Deliberately failed install and cleanup | Skipped | No failed install induced and no remote bootstrap artifacts removed. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Literal-token upgrade and NCPA result parity | Skipped | No config/app upgrade or live NCPA metric comparison executed. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Nagios reads applied live hosts.cfg at 0640 | Skipped | Mode is proven locally in the apply test; this app revision was not applied to the live guest. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |

## Deviations from the plan

The configured guest was stopped/aborted, explaining the prior refused SSH
inspection. With existing VM authorization, it was started after capacity checks.
No snapshot reset, fresh provisioning, app sync, scan, migration, deployment,
cleanup or live resource replacement was done. A single empty permission-probe
file was created and removed. Guest is left running for continued inspection.

The final two equivalence assertions were strengthened after the full gate;
only test files changed, and both tests passed on their named checkpoint.
No extra full-suite rerun was needed for unchanged application source.

## Follow-up

- [Issue #129](https://github.com/esfen14/Pinpoint/issues/129) remains open: implement secure credential transport and an ownership-compatible installer mechanism; repeat all skipped live cases and process inspection.
- The concrete installer handoff is in [the transport plan](../../plans/Issue_129_Check_Secret_Transport.md). No installer code or permissions were changed.
- CI, PR evidence publication and reviewer approval are still outstanding.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
