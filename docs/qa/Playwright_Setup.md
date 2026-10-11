# Playwright Setup for QA E2E Testing

Pinpoint uses Playwright for end-to-end (E2E) testing. This document covers setup and running specs against a local lab or mocked backend.

**Status: incomplete draft.** The current admin scaffold has not passed a live
smoke test. Restricted-role setup, forced password changes and mocked-backend specs
remain unfinished. Do not run against a lab owned by another teammate. The baseURL
is not network isolation; an OS/container egress boundary must be established before
agent browser exploration. Login captures are disabled, and missing credentials fail
closed rather than using a default password. No live run is authorized while the
owner investigates #86.

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
- **Isolation/Concurrency:** `1` worker, Chromium only, JSON reporter.
- **Excluded Artifacts:** Raw traces, videos, HAR files, screenshots, and auth state `.auth/` are git-ignored. Sanitized excerpts may be copied to reports.

## 3. Auth State & Environment Variables

Playwright logs in using predefined roles via setup projects (e.g., `setup-admin`) and saves auth state into `.auth/`.

Set the credentials for your target environment before running:
```bash
export PINPOINT_ADMIN_USER="..."
export PINPOINT_ADMIN_PASSWORD="..."
```

## 4. Running the Tests

To run the full suite:
```bash
cd client/
npx playwright test
```

To run a specific test by case ID title (e.g. J1-04):
```bash
npx playwright test -g "J1-04"
```

## 5. Automation Guidelines

- **Self-Healing:** Not used. We want brittle tests to fail and reveal regressions.
- **Reporting:** Extract failures from the JSON report to build sanitized markdown entries for `docs/test-runs/<date>-<slug>/REPORT.md`.
- **Safety:** Do NOT commit `.auth/*` or raw dumps containing passwords.
