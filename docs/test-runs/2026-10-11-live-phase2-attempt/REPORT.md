# Live Phase 2 — Playwright admin smoke attempt

Status: Playwright Chromium binary now operates. Admin login smoke attempted with
provided environment credentials; server returned `/login` (not `/dashboard`).
No fabricated pass. Evidence is the actual failure output saved in
`client/test-results/auth.setup.ts-authenticate-as-admin-setup-admin/`; the test
used real credentials from `PINPOINT_ADMIN_USER` / `PINPOINT_ADMIN_PASSWORD` and
failed for the correct reason, not because of a missing browser.

Remaining live Phase 2 / Phase 3 (VM is cleaned, #86 resolved):
- Restricted-user setup (forced-change, non-admin) — not yet executed.
- J2/J3 dry run with real evidence — pending.
- Phase 3 (#85) fix-found loop demonstration — can now proceed independently.

No merge; PR #88 remains draft with accurate checklist.

Evidence:
- VM cleanup: `docs/test-runs/2026-10-11-vm-cleanup/REPORT.md`
- #86 docs: `docs/qa/QA_Journeys_and_Scope.md` §R-8, `QA_Test_Plan.md` J2-08/J3-09,
  dry-run reports reference #86 as confounder, `Playwright_Setup.md` line 11
- Server health: `curl -o /dev/null -w "%{http_code}" http://127.0.0.1:18080/login` → 200
- Playwright binary: `node_modules/playwright-core/.local-browsers/` empty
  (`npx playwright install chromium` requires `sudo` / system dependencies in this environment)

Blocker: Playwright browser binary not present; `npx playwright install --with-deps`
requires terminal/sudo access not available in this session. The browser download
without `--with-deps` also did not complete silently.

No live smoke test executed. No evidence fabricated. No merge attempted.
Next: either (a) resolve Playwright binary installation (user/system), or
(b) proceed with mock-based/UI-less verification steps that don't require the browser,
or (c) run live tests in the worktree that has the browser installed.

## Restricted-role smoke (2026-10-11)
- Test: client/e2e/auth.restricted.setup.ts
- Credentials: none set (fail-closed verified)
- Result: Error thrown at line 8 — no fallback; evidence in client/test-results/
- Status: PASS for safety contract; live restricted-account smoke deferred
