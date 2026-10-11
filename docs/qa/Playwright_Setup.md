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
scripts/vmlab setup-restricted
scripts/playwright-lab
```

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
