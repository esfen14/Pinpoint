# Test run: issue-164-identity-review

| | |
|---|---|
| Date | 2026-10-15 |
| Commit tested | Product implementation `d8aac3e4` (unchanged through `80a10fb1`); Docker/browser harness `80a10fb1`; metadata-only checkpoint `7fce5bd4` |
| Plan | [Issue #164, sections E–H](https://github.com/esfen14/Pinpoint/issues/164) |
| Tester | Codex, actual automated executions |
| Environment | Ubuntu 22.04 Docker appliance image; real Nagios Core 4.5.11; Python 3.14; fresh migrated and seeded SQLite databases; Chromium through Playwright 1.64.0. Exclusive `pinpoint-issue164` project, API on loopback 8164 and Vite on 5164; separate isolated private target network. Shared `pinpoint-lab` untouched |
| Raw evidence | Local host `/home/paeng/pinpoint-test-results/issue164/`; `success/`, `notice/`, `warning/` screenshots; `verify-all.log`. Raw evidence is not committed |

## Result

**Overall: Pass for the scoped implementation and Docker acceptance.** Three
complete browser journeys passed: normal merge, normal merge opened from the
participating device notice, and saved merge with a real configuration failure.
Full local verification passed. CI and human approval are separate PR gates;
this report does not establish reviewer approval or production deployment.

Totals: Pass 13, Fail 0, Blocked 0, Skipped 0 scoped cases. The backend suite
separately reports 14 existing skips.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| Identity-only count and separate table | Pass | Browser showed Needs Review (1) while API also contained an unresolved SERVICE_CHANGED item. Source was address-unknown and absent from the default Monitored host table. Unit tests cover all five identity kinds | #164 |
| Recognized address move | Pass | Fixture supplied two controlled observations with the same hardware identity at different addresses to the real reconciler. Stable ID remained unchanged, record count remained one and no review was created | #164 |
| Ambiguous discovery produces review | Pass | A contrasting controlled identity at the current address created a new record and an IP-reuse review; previous holder became Address unknown. No automatic merge | #164 |
| Comparison and insufficient candidates | Pass | Browser opened generated one-candidate review, read confidence/identifiers, explicitly loaded real address history and used discovered lookup by ID to add the other record | #164 |
| Explicit source/target and confirmation | Pass | Both selectors initially blank. Browser chose source ID 1 and target ID 2; confirmation contained address retention, source leaving monitoring, target precedence, original snapshot names and no undo. `notice/issue164-comparison.png` | #164 |
| Cancellation is read-only | Pass | Escape closed comparison, restored focus to Review, and the unresolved review IDs remained unchanged; unit tests separately assert no mutation request on cancellation | #164 |
| Linked device notice | Pass | Forced one real Nagios check of the controlled address-unknown source, polled a genuine status snapshot, selected Not monitored, opened its information drawer and followed This device needs identity review into the same comparison | #164 |
| Keyboard, themes and narrow display | Pass | Browser verified dialog focus, Escape/restore, reverse-Tab focus on confirmation, real light/dark preference changes and no horizontal drawer overflow at 560px. `notice/issue164-light.png`, `notice/issue164-dark.png` | #164 |
| Successful merge and refresh | Pass | Browser observed successful POST, one submission, closed comparison, empty review state and persisted source MERGED / unchanged target ID and current address. Post-run fixture verified port 8080 moved, reviews resolved, source removed from generated config, surviving target retained. `notice/issue164-success.png` | #164 |
| Real Nagios config validation | Pass | Normal merge applied through existing reconciler/writer. Direct `nagios -v` reported 0 errors and 0 warnings after merge | #164 |
| Saved merge with unavailable Nagios | Pass | Recreated only the expendable appliance, seeded the same fixtures and stopped its Nagios. Browser observed HTTP success with config_ok false, accurate Merge saved / Nagios configuration warning, empty reviews, source MERGED and exactly one merge POST. `warning/issue164-warning.png` | #164 |
| Restore configuration without repeating merge | Pass | Restarted Nagios and invoked existing reconciliation; postconditions passed again and `nagios -v` reported 0 errors/warnings. Subsequent reconcile returned success with no change | #164 |
| Automated regression and contracts | Pass | `scripts/verify.sh all`: 3302 backend passed, 14 skipped; 701 frontend passed; docs/drift checks, TypeScript/Vite build and lint passed (0 errors, 28 pre-existing warnings). Includes identity routes/matching and separate lookup coverage. Focused comparison suite: 15 passed, including permission gates, unavailable evidence, retries, self/invalid/stale choices and duplicate-submit guard | #164 |

## Reproduction

Use the opt-in [fixture](../../../lab/identity_review_fixture.py) on a **fresh,
exclusively owned disposable appliance**, with `PINPOINT_IDENTITY_LAB=1` and
`PINPOINT_SCHEDULER=0`. `seed` drives the reconciler and applies real Nagios
configuration; it refuses a populated discovery inventory. `prime-source`
optionally produces the genuine source snapshot for notice coverage. No network
scan is performed. The isolated target address is fixed in the fixture; provision
the target on the matching isolated network.

Supply lab credentials privately in `PINPOINT_ADMIN_USER` and
`PINPOINT_ADMIN_PASSWORD`; never enable trace/login capture. Set
`ISSUE164_LAB_URL` to the loopback frontend and `ISSUE164_SOURCE_ID` /
`ISSUE164_TARGET_ID` from seed's nonsecret output. Run:

```bash
cd client
ISSUE164_CHECK_NOTICE=1 npx playwright test --project=issue-164-live --reporter=list
```

Use a fresh disposable fixture and stop **only that appliance's** Nagios for the
warning journey, then run with `ISSUE164_EXPECT_CONFIG_WARNING=1` instead of
`ISSUE164_CHECK_NOTICE`. Restart Nagios and reconcile afterward; do not repeat
the saved merge. `verify` checks the post-merge database/configuration invariants.

## Deviations from the plan

- Controlled discovery observations and a real Docker Nagios daemon were used;
  physical DHCP changes, installer/systemd behavior, performance and production
  deployment were not exercised or claimed.
- The stock Docker entrypoint starts its opt-in scheduler before fresh migration;
  provisioning disabled that scheduler before initialization and used explicit
  status polls. No product or shared lab configuration was changed for this.
- One restoration command applied reconciliation but its shell-quoted assertion
  failed with NameError afterward. The fixture verification and Nagios validation
  passed; a clean subsequent reconcile confirmed success with unchanged config.
- No new dependencies, permissions or migrations were introduced. No matching
  rules, merge validation or configuration application code was changed.

## Follow-up

- Required CI checks and reviewer approvals must be observed on the PR.
- No product defect was found in these scoped journeys.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No raw addresses outside the documented lab range in this report
- [x] Evidence is referenced by name and location, not pasted
