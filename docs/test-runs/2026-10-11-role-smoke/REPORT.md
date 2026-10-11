# Test run: role-smoke

| | |
|---|---|
| Date | 2026-10-11 |
| Commit tested | `c8fcd586cf2072099d1ece0caf8482a0e2f67b17` |
| Plan | `docs/qa/QA_Test_Plan.md` |
| Tester | Codex, under the lab owner's explicit release |
| Environment | Running VirtualBox appliance `pinpoint-appliance-45`; Chromium 156.0.8078.4; inherited appliance database; browser container had Docker networking disabled |
| Raw evidence | Ignored `client/test-results/playwright-results.json` on the test host; no trace, screenshot or video captured |

## Result

**Overall: Pass.** Both role setup paths and both role smokes passed. The restricted
account was provisioned as seeded Staff, completed its forced password change, opened
only General Settings, redirected away from Dashboard and received HTTP 403 from a
Dashboard API route.

Totals: Pass 2, Fail 0, Blocked 0, Skipped 0.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| J1-04 | Pass | Administrator setup authenticated and saved isolated auth state; the Dashboard displayed Network Status Overview and Active Alerts. | #63 |
| J9-04 | Pass | Staff setup displayed and completed the forced password-change window; `/dashboard` redirected to `/settings`, only General Settings was offered, and `GET /api/system/dashboard/status` returned 403. | #63, #93 |

## Deviations from the plan

This run covers the browser-role portion of J1-04 and J9-04 only. It does not claim
the rest of either broader case. Chromium ran in a `--network none` container; a
private Unix socket bridged only the documented loopback application origin into the
container. The exact Playwright JSON reporter output remains ignored as raw evidence.

## Follow-up

- No product defect was found.
- The temporary Staff account remains in the disposable appliance. A fresh appliance
  reset removes it; `scripts/vmlab setup-restricted` safely resets it before another run.
- Continue the independent J2/J3 acceptance cases; this report does not change their
  prior partial results.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
