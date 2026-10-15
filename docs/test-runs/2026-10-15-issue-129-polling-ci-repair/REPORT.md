# Test run: issue-129 polling migration CI repair

| | |
|---|---|
| Date | 2026-10-15 |
| Commit tested | Repair working tree based on `5bb6f7a0`, adding merge revision `a129f6d23901` |
| Plan | [Issue #129](https://github.com/esfen14/Pinpoint/issues/129) migration and CI finish condition |
| Tester | Codex |
| Environment | Isolated local suites, temporary SQLite databases; no live database/appliance changes |
| Raw evidence | Git-ignored `test-results/issue-129/`: `polling-merge-red.log`, `polling-merge-focused.log`, `polling-merge-backend.log`, `polling-merge-docs.log`. Failing remote [run38698563725](https://github.com/esfen14/Pinpoint/actions/runs/38698563725). |

## Result

**Overall: Partial.** The latest main merge introduced the independent data-polling head alongside the NCPA convergence head. Local repair and verification pass; publication/current-head GitHub CI remain pending owner push confirmation. Previous green CI and live reports remain attributed to their exact earlier commits.

Totals: Pass 3, Fail 0, Blocked 1, Skipped 1.

## Cases

| Case | Result | Notes | Issue |
|---|---|---|---|
| Reproduce latest CI failure | Pass | Current CI failed collection with MultipleHeads f129a79e6301/f6d2c8a1b390. Extended six-entry upgrade regression failed with the same error before fix. The earlier f2c430c7 head had all three CI jobs green before the subsequent main merge. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Upgrade and data-preservation repair | Pass | Added no-op multi-bind join a129f6d23901, preserving all published ancestors.45 focused migration/upgrade tests pass. Six prior entry points reach one head in both binds; port/interface/recipient/history data and a custom120-second polling interval survive downgrade/re-upgrade. Existing settings receive the expected60-second default when polling migration is first applied. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Backend and docs verification | Pass | scripts/verify.sh backend:3002 passed/14 existing skips. Docs and diff checks pass. Frontend unchanged; docs/frontend CI on5bb6f7a0 passed. No tests removed/weakened or workflows changed. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Current-head CI | Blocked | New repair remains local until requested owner push confirmation; existing remote backend remains red. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Live upgrade and frontend rerun | Skipped | Repair changes migration graph, regression fixtures and documentation. No new appliance migration or live acceptance rerun. Frontend source unchanged and latest remote frontend CI passed. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |

## Follow-up

Push only after owner confirmation and verify all current-head CI. Application PR remains ready for review; no PR merge performed. The paired installer helper remains the documented deployment dependency.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
