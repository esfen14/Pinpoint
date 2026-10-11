# Issue #87: Chore: rename /topology route and file to /system-status

Branch: `issue-87-system-status-route`
Status: in-progress

## Finish condition

- [x] The System Status page is served at `/system-status`; `/topology` is no longer a supported or registered browser route.
- [x] `TopologyPage.tsx` and its exported component are renamed to System Status terminology, with imports and route wiring updated.
- [x] Sidebar/navigation, page access rules, tests, and browser-route documentation use `/system-status` and System Status terminology.
- [x] Relevant specifications and `Implementation_Status.md` no longer describe the stale topology route/file naming as an open mismatch.
- [x] Frontend and documentation verification pass.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Rename the supported route | System Status browser route | App routing test; frontend verification |
| Rename the page file/component | System Status terminology | TypeScript import/component test; source inspection |
| No compatibility route | `/topology` unsupported | App route test and frontend-route drift check |
| Navigation and access consistency | Sidebar/navigation/access docs | Page-access/sidebar tests and docs verification |
| Clear stale implementation mismatch | Specifications/status | Updated specifications and docs verification |

## Plan

1. [x] Add failing route/access tests in `client/src/test/App.test.tsx` and the relevant page-access tests for `/system-status` and removal of `/topology`.
2. [x] Rename `client/src/pages/TopologyPage.tsx` to `SystemStatusPage.tsx`, rename its export, and update `client/src/App.tsx`, `client/src/lib/pageAccess.ts`, `client/src/components/layout/Sidebar.tsx`, and `client/src/components/layout/Header.tsx`.
3. [x] Update `spec files/Frontend_Modules_and_Routes.md` and `spec files/Implementation_Status.md` to remove the completed stale-name mismatch.
4. [ ] Run focused frontend tests, docs verification, and `scripts/verify.sh all`; re-read issue #87, remove this progress file, and open a PR when every finish-condition item is proven.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Added failing `/system-status` route and page-access tests, then renamed the page/route/navigation/access wiring and updated the specifications. | Focused Vitest, `scripts/verify.sh docs`, `scripts/verify.sh frontend` | Green: 22 focused tests; docs route-drift validation green; frontend suite/build green (pre-existing warnings only). |

## State for the next session

- Last check run (exact command): `scripts/verify.sh docs && scripts/verify.sh frontend`
- Result (first failing lines, or "green"): Green. Docs route-drift validation reports 14 matching routes; frontend test/build green with 25 pre-existing warnings.
- Hypothesis: Renaming only the supported page and its route references satisfies the issue; dormant `client/src/pages/wagpakielaman.tsx` is excluded topology source and outside scope.
- Next action (one specific step, not "continue"): Checkpoint this round, run `scripts/verify.sh all`, then re-read issue #87 before removing this progress file and opening the PR.

## Decisions and notes

- The user confirmed the system is unreleased, so `/topology` needs no redirect or alias.
- The network topology feature remains excluded; System Status is the supported service-status page.
