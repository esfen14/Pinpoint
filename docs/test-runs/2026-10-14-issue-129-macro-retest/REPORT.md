# Test run: issue-129-macro-retest

| | |
|---|---|
| Date | 2026-10-14 |
| Commit tested | `fd5f0f62` initial macro regression; `4a784b83` merged-source regression, process diagnostic and full gate |
| Plan | [Issue #129 transport plan](../../plans/Issue_129_Check_Secret_Transport.md) |
| Tester | Codex |
| Environment | Local isolated Python/React suites; Linux process diagnostic with a synthetic credential and fake NCPA executable; no real credentials, live Nagios execution or network checks |
| Raw evidence | Git-ignored `test-results/issue-129/`: `macro-secrets-retest.log`/`.xml`, `merged-macro-tests.log`, `post-merge-verify-all.log`, `process-diagnostic.txt` |

## Result

**Overall: Partial; process-secrecy criterion failed.** Macro/config/snapshot
regressions and the full merged-source gate pass. The diagnostic demonstrates
why those passing tests do not complete the macro-secret acceptance criteria.

Totals: Pass 3, Fail 1, Blocked 2, Skipped 0.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| Macro/config/NCPA/snapshot regressions before merge | Pass | Seven modules: 332 passed in 26.88 s; JUnit generated. `macro-secrets-retest.log`, `macro-secrets-retest.xml`. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Merged macro and notification regressions | Pass | Preserved both appended test blocks while merging main; added notification-template/email regressions to the same target: 379 passed in 29.23 s. `merged-macro-tests.log`. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Full merged-source verification | Pass | On 4a784b83, `scripts/verify.sh all`: 2719 backend passed / 14 skipped, 554 frontend passed, build successful, lint 0 errors / 29 warnings. `post-merge-verify-all.log`. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| No credential in an expanded check process's arguments | Fail | Used the actual NCPA command renderer and secret substitution, simulated ARG/USER macro expansion, executed a fake persistent NCPA process and inspected `/proc/<pid>/cmdline`. The synthetic credential was absent from the protected host argument but present in process argv after expansion. No real credential or live Nagios/network check used. This is a diagnostic of the existing renderer, not an engine-level acceptance run. `process-diagnostic.txt`. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| PR CI | Blocked | Draft PR #161 has no checks because the remote head conflicts with main. Conflict is resolved locally; pushing the verified merge awaits owner confirmation. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Installed ownership and secure transport acceptance | Blocked | Separate installer helper scope is not approved; NCPA/SMB secure input or adapter remains unimplemented. Prior installed compatibility evidence is in the linked report below; no live config apply attempted in this run. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |

## Deviations from the plan

The final plan checkbox cannot be completed: process secrecy is disproved by the
synthetic diagnostic, installed ownership/transport work is incomplete, and live
acceptance and reviewer approval remain outstanding. The PR was opened as a
**draft**, retaining its progress file.

New main changes (#144 History recovery and #152 HTML alert email) caused an
append-only test conflict. The first edit left a separator and failed collection;
the conflict was restored and corrected, retaining both branches' tests. The
subsequent focused/full checks pass. No workflows, installer files, test
expectations or permissions were weakened.

## Follow-up

- [Draft PR #161](https://github.com/esfen14/Pinpoint/pull/161): push local merge only after confirmation, then observe CI.
- Implement supported secure credential transport and obtain authorization for the separate installer's scoped ownership-preserving helper before claiming final acceptance.
- Prior [installed compatibility report](../2026-10-14-issue-129-resource-compatibility/REPORT.md) records the service-user ownership limitation and skipped live cases.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
