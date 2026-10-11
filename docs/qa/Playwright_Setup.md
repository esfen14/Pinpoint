# Playwright Setup for QA E2E Testing

Pinpoint uses Playwright for end-to-end (E2E) testing. This document covers setup and running specs against a local lab or mocked backend.

**Status:** administrator and restricted Staff smoke paths passed on the VM lab on
2026-10-11. Mocked-backend specs remain unfinished. Do not run against a lab owned
by another teammate. Login captures are disabled, and missing credentials fail
closed rather than using a default password.

## 1. Prerequisites

You will need a Linux environment (Debian 13 or Ubuntu 24.04). Playwright uses Chromium and requires system libraries.

```bash
cd client/
npm ci # installs the committed exact Playwright pin and lockfile
```

Install Playwright browsers and dependencies:
```bash
npx playwright install --with-deps chromium
```

## 2. Configuration Highlights

- **Config File:** `client/playwright.config.ts`
- **Exclusion:** Vitest excludes the `client/e2e/` folder (configured in `client/vitest.config.ts`).
- **Target:** Playwright uses `baseURL` `http://127.0.0.1:18080`.
- **Isolation/Concurrency:** `1` worker, Chromium only, JSON reporter. The live
  runner uses Docker `--network none` and a private Unix-socket bridge exposing only
  `http://127.0.0.1:18080` inside the container.
- **Excluded Artifacts:** Raw traces, videos, HAR files, screenshots, and auth state `.auth/` are git-ignored. Sanitized excerpts may be copied to reports.

## 3. Auth State & Environment Variables

### Authentication handling contract

Live QA uses only disposable lab accounts; it never uses a personal,
production, or GitHub credential.  `scripts/vmlab setup-admin` creates the
lab administrator state after a fresh appliance, and
`scripts/vmlab setup-restricted` creates/resets the temporary Staff account.
Their email/password files live only in the private vmlab state directory with
owner-only permissions.  The runner reads them at execution time and passes
them into its no-network container as environment variables; it does not echo
them, write them to the repository, or add them to the report.

Keep these boundaries for every live run:

- Never print credential files, command lines containing their values, cookies,
  Playwright storage state, traces, screenshots, HAR files, or raw API dumps.
- Do not commit `.auth/`, `client/test-results/`, private vmlab state, or a
  `.env` file containing lab authentication.  They are runtime-only evidence.
- The live runner has `--network none`; its Unix-socket bridge can reach only
  the documented local appliance origin.  Do not replace it with a browser or
  runner that has broader network access.
- A fresh/reverted appliance invalidates its accounts.  Run the setup helpers
  again, and do not reuse credentials copied from an older run.
- Reports state only that the expected role authenticated or was refused.  They
  reference the private evidence location without including usernames,
  passwords, cookies, or session identifiers.

Playwright uses separate `setup-admin` and `setup-restricted` projects and saves
their auth state into separate ignored files under `.auth/`. The restricted setup
must observe and complete the forced password-change screen before its smoke runs.

On the VM lab, create or reset the temporary Staff account before every live run:

```bash
scripts/vmlab setup-restricted
```

This command is safe to repeat. It stores the account email, temporary password and
post-change password with mode 0600 in the existing private vmlab state directory.
It disables email alerts and assigns the seeded Staff role, which has no administrator
permissions. A fresh appliance reset removes the account; rerun the command afterward.

Set the credentials for your target environment before running:
```bash
export PINPOINT_ADMIN_USER="..."
export PINPOINT_ADMIN_PASSWORD="..."
export PINPOINT_RESTRICTED_USER="..."
export PINPOINT_RESTRICTED_PASSWORD="..."
export PINPOINT_RESTRICTED_NEW_PASSWORD="..."
```

## 4. Running the Tests

To run the live suite with the required egress boundary:
```bash
scripts/vmlab status                 # appliance + os-nagios-ready snapshot must exist
scripts/vmlab targets up
scripts/vmlab fresh                  # only when a clean faithful-lane baseline is required
scripts/vmlab setup-admin            # after fresh, before normal authenticated cases
scripts/vmlab setup-restricted
scripts/playwright-lab
```

Do not start these commands if another tester owns the VM lab.  If `status`
reports a missing appliance or snapshot, recover it through
[VM Lab Plan §4](../plans/VM_Lab_Plan.md#4-steps-to-get-running) rather than
pointing Playwright at an ad-hoc environment.  `scripts/vmlab fresh` is
destructive to the current appliance state; use it only for an approved clean
baseline.

Playwright CLI filters may be passed through, for example
`scripts/playwright-lab --project admin -g J1-04`.

`scripts/playwright-lab` uses the locally installed exact Chromium build and a local
Node image; it does not download packages. Raw JSON stays under ignored
`client/test-results/`. Use direct `npx playwright test` only for mocked specs that
do not handle live credentials.

To run a specific test by case ID title (e.g. J1-04):
```bash
npx playwright test -g "J1-04"
```

## 5. Automation Guidelines

- **Self-Healing:** Not used. We want brittle tests to fail and reveal regressions.
- **Reporting:** Extract failures from the JSON report to build sanitized markdown entries for `docs/test-runs/<date>-<slug>/REPORT.md`.
- **Safety:** Do NOT commit `.auth/*` or raw dumps containing passwords.
