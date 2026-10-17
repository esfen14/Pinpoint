# Test run: issue-191-accounts

| | |
|---|---|
| Date | 2026-10-17 |
| Commit tested | `2688e430` |
| Plan | [Account creation investigation](../../plans/Issue_191_Account_Creation_Investigation.md) |
| Tester | Codex |
| Environment | Local Linux, headless Chromium, Vite on loopback, real Flask API with fresh temporary file-backed SQLite system/history databases; scheduler disabled; Nagios writer stubbed |
| Raw evidence | Local `/tmp/issue191-browser.cjs`, `/tmp/issue191-local-server.py`, `/tmp/issue191-local-server.log`; isolated verification logs `/tmp/issue-191-frontend.log` and `/tmp/issue-191-all.log` |

## Result

**Overall: Pass for scoped account-creation checks.** Real browser interactions
created two additional accounts through the real API and both remained visible
after reload. No VM/Docker lab, live Nagios, installer, or physical network was used.

Totals: Pass 5, Fail 0, Blocked 0, Skipped 0.

## Cases

| Case | Result | Notes | Issue |
|---|---|---|---|
| Open Add User while role options are delayed | Pass | Filled required fields with a policy-compliant matching password; Save disabled until roles arrived | [#191](https://github.com/esfen14/Pinpoint/issues/191) |
| Save after default role arrives | Pass | Role showed Administrator and Save enabled; clicking returned 201 and the first new account appeared | #191 |
| Add another account without reloading | Pass | Selected Viewer and Inactive; Save enabled, POST returned 201, second new account appeared | #191 |
| Reload persistence and account count | Pass | Both new rows remained visible after reload; real GET returned total 3, including bootstrap administrator; Viewer/Inactive values persisted | #191 |
| Desktop viewport | Pass | All preceding interactions completed at 1366 × 768 | #191 |

## Deviations from the plan

The first browser harness used a shared in-memory SQLite connection with a
threaded server. Concurrent development-mode requests caused harness transaction
interference and a reload failure. That attempt did not establish product
persistence. The corrected run used separate file-backed temporary databases
and passed all five checks above. The harness success line still said
“in-memory”; the tested configuration was file-backed SQLite.

The original reporter's precise trigger remains unconfirmed: manually changing
to a different role can work around the reproduced timing defect. Baseline
isolated regression failed at the expected enabled-button assertion; the fix
passed all 30 account-page tests, including repeated saves, no-role feedback,
password-policy/mismatch guards and rejected-save retry. The focused backend
module passed 74 tests, including persisted creation of two additional users.

## Follow-up

Live Nagios contact application, an installed appliance, other viewport sizes
and the reporter's original data were not tested. The issue requests account
creation; no monitoring configuration behavior was changed.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside loopback or the documented lab range
- [x] Evidence is referenced by name and location, not pasted
