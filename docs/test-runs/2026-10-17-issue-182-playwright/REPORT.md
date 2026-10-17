# Issue #182 Playwright browser walkthrough

| | |
|---|---|
| Date | 2026-10-17 |
| Product commit tested | `910d6f99` on the retained fresh appliance; subsequent branch changes were documentation only |
| Browser harness | Base `8a6b11de` plus `client/e2e/remote-restart.lab.spec.ts` and its opt-in project in this change; spec SHA-256 `50cc01d30b0505bb700a57c2a0519f0df252c6843bcba3224d8a79dbae29aad4` |
| Plan | [Remote Restart Acceptance](../../../server/tests/plans/REMOTE_RESTART_ACCEPTANCE.md), RR-12 |
| Tester | Codex using Playwright 1.64.0 / installed Chromium |
| Environment | Exclusively owned issue182 Ubuntu appliance and target, isolated 10.77.0.0/28 virtual network; existing deployed target 10.77.0.2 |
| Raw evidence | Local ignored `client/test-results/playwright-results.json`, five `issue182-*.png` screenshots; `/tmp/issue182-playwright.log` |

## Result

**Overall: Pass for RR-12.** Three real-browser tests passed in 26.0 seconds, with no failures or skips. This completes the browser case left blocked in the [earlier live acceptance run](../2026-10-17-issue-182-remote-restart/REPORT.md). Human security review/reviewer approval remains an external merge requirement.

## Cases

| Case | Result | Observed behavior |
|---|---|---|
| RR-12a | Pass | Loading state and no editable save controls after a deliberately injected load failure; Retry loaded real settings. Empty enabled list produced the real server validation error while retaining the switch. Real saves persisted the enabled switch and sorted service list across close/reopen, with the cleanup/redeploy notice. Browser cleanup displayed the warning, removed bootstrap artifacts, cleared both credential fields, and the full deployment wizard checked real SSH credentials and completed successful redeployment. Reopening settings showed the restored original list and disabled switch. |
| RR-12b | Pass | Remote unit text field rejected a hostile name through real server validation, retained the entered value and associated the error with its field. Creating, editing and reloading a disabled remote action preserved the chosen unit. Local unit control offered only the placeholder and nagios; saved/reopened local action retained nagios. Both browser-created actions were deleted. |
| RR-12c | Pass | An actual account with only remediation.view could read actions but saw no Add/Edit controls; switches were disabled. Real settings GET/PUT and action creation returned 403. Direct NCPA navigation redirected to the permitted Remediation page with no restart control. |

## Isolation and evidence limits

Both guests passed process/controller/runtime-forward ownership preflight. Chromium ran as the host user in a Docker container with networking disabled; a private mode-600 Unix socket forwarded only to the owned appliance HTTP endpoint. Credentials were read from private mounted runtime state inside the container, never command-line arguments. Login traces/video/screenshots were disabled. Five screenshots were captured only after login, with no filled credential forms. Raw browser artifacts are ignored and are not committed.

Only the initial settings-load failure was intercepted (an explicit synthetic HTTP 500). Retry, validation, saves, persistence, cleanup, SSH credential checking, deployment and restricted authorization all used the real appliance APIs. The local restart action stayed disabled and did not restart Nagios. This browser run does not claim another Nagios-generated failure chain.

## Cleanup and follow-up

The original two-service list is restored in Pinpoint and in the target's root-owned file; remote restart and all test actions are disabled. Browser actions were deleted and the read-only fixture account was deactivated through the supported API. Helper ownership/mode remains root:root 755 and list root:root 644. Owned guests are shut down through guarded endpoints; disks/private runtime state retained. No KVM module was unloaded for this run.

- Pending: human security review/reviewer approval before merge; current-head CI is tracked on [PR #190](https://github.com/esfen14/Pinpoint/pull/190).
- Frontend verification: `scripts/verify.sh frontend` passed (875 tests, build, lint with 30 warnings and zero errors); final docs gate also run before checkpoint. No backend product source changed; prior full gate and CI were green.
- Automated browser scaffolding safety: 8 tests passed (`scripts/test_playwright_safety.py`).

## Sanitization

No credentials, tokens, private keys, raw database contents or raw screenshots are committed. Addresses are restricted to documented lab scope; raw evidence is referenced by name only.
