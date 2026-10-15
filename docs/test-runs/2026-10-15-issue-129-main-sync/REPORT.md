# Test run: issue-129 main synchronization

| | |
|---|---|
| Date | 2026-10-15 |
| Commit tested | Merge working tree: issue head `e5c7e6f0` and main `9ce590eb`, with stored-port inventory integration fix |
| Plan | [Issue #129](https://github.com/esfen14/Pinpoint/issues/129) D/G/H; [transport plan](../../plans/Issue_129_Check_Secret_Transport.md) |
| Tester | Codex |
| Environment | Local isolated backend/frontend verification; no lab mutation in this merge run |
| Raw evidence | Local git-ignored `test-results/issue-129/`: `main-merge-inventory-red.log`, `main-merge-focused.log`, `main-merge-verify-all.log`, `main-merge-final-docs.log`. |

## Result

**Overall: Partial.** Main synchronization retains issue #128 metric inventory/process defaults and issue #129 protected credential transport, transactions and stored ports. Full verification passes: 2784 backend tests/14 existing skips, 568 frontend tests, build/docs passed and lint 0 errors/29 existing warnings. Publication/current-head CI and required human reviews remain outstanding.

Totals: Pass 3, Fail 0, Blocked 1, Skipped 1.

## Cases

| Case | Result | Notes | Issue |
|---|---|---|---|
| Stored-port inventory integration regression | Pass | New parameterized regression failed for stored 5703 versus global 5693 before fix; legacy no-port fallback passed. New inventory calls use the stored deployed port, retaining the default when missing. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Merged focused regressions | Pass | 344 passed across config, resource/helper, NCPA/native adapter, device-config and custom checks. Both appended test/report blocks were retained during conflict resolution. No tests removed/weakened. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Full verification | Pass | scripts/verify.sh all: 2784 backend passed/14 skipped, 568 frontend passed; build/docs passed; lint 0 errors/29 existing warnings. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Current-head CI and required reviews | Blocked | Published e5c7e6f0 conflicts with main9ce590eb and has no CI runs. Local merge needs separate push approval. App/installer human approvals are still absent. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Merged-source live journeys | Skipped | Earlier mandatory live proof belongs to c9f8e263 functional source. This merge run does not upgrade the guest or claim a repeat of that live acceptance. Previous lab restoration is unchanged. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |

## Deviations from the plan

Owner authorized pushing the two evidence commits. Both were pushed. Current main had meanwhile merged #128, creating conflicts in the shared renderer, its tests and test-run index and preventing CI. Resolved locally within the existing issue branch. New bounded inventory probing was integrated with the already-approved stored-port behavior; this changed no credential transport or helper privilege.

## Follow-up

- Publish the locally verified merge only after push confirmation, then check CI.
- Obtain application and installer approvals; keep both PRs draft. No PR merge performed.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
