# Test run: issue-117-main-sync

| | |
|---|---|
| Date | 2026-10-15 |
| Commit tested | `4981a70e7c25ab3baec694a8d9ea3ad1a3d53bbe`; tests ran on its identical merged application/migration source before the checkpoint |
| Plan | [Manual Topology Acceptance](../../../server/tests/plans/MANUAL_TOPOLOGY_ACCEPTANCE.md), owner-requested continued testing after current-main integration |
| Tester | Codex |
| Environment | Isolated local pytest/Vitest; Chromium/Playwright through real Vite/Flask HTTP and Nagios Core 4.5.11 in disposable Ubuntu 22.04 containers; routed targets within `10.77.0.0/28`; loopback HTTP management bridge |
| Databases | Private dual-bind SQLite migrations from both published heads; browser databases upgraded to joined head `c117e6a9d042`, with checked HARD-UP baseline history fixtures |
| Raw evidence | Local host `/tmp/issue117-main-sync-focused.log`, `/tmp/issue117-convergence.log`, `/tmp/issue117-merge-red.log`, `/tmp/issue117-main-sync-all.log`; browser `/tmp/issue117-main-sync-browser.log`, `/tmp/issue117-live-cca82448/` (`browser.log`, `server.log`, `nagios-final.log`) |

## Result

**Overall: Partial.** Focused combined-feature and populated migration tests pass;
the real browser/backend/Nagios retest and full local verification pass. Final CI is
tracked on [PR #174](https://github.com/esfen14/Pinpoint/pull/174). Human review,
production deployment and SMTP inbox delivery are outside this run.

Totals: Pass 5, Fail 0, Blocked 0, Skipped 1.

## Cases

| Case | Result | Notes (observed behavior; evidence) | Issue |
|---|---|---|---|
| S117-01 | Pass | 102 focused parent/API/writer/migration/escalation/remediation-rendering tests pass. Existing feature suites retained. `issue117-main-sync-focused.log`. | — |
| S117-02 | Pass | Populated installs at both `b117d9a2c041` and `99f584ed8151` upgrade to one joined head on both binds. Existing parent pairs, escalation choices, remediation actions/runs and device rows match exactly; history marker survives. Downgrading just the join and re-upgrading preserves both schemas/rows. New tests first failed with multiple heads before the generated join. | — |
| S117-03 | Pass | Combined candidate contains multiple parents, scoped escalation and an enabled host remediation handler. Removing only the added parent line reproduces the baseline fingerprint. No parent mutation changes the other generated features. | — |
| S117-04 | Pass | Real browser/Flask/Nagios retest: Topology multi-parent save/reload/edges; cycle 400 with draft retained; Inventory clear/reload/set with persistent success confirmation; cross-page consistency; restricted UI and direct PUT 403; zero page errors. Actual shared writer validates/reloads successful saves. Owned containers/networks removed in finally. `browser.log`, `issue117-main-sync-browser.log`. | — |
| S117-05 | Pass | `scripts/verify.sh all`: 3338 backend tests passed / 14 skipped; 54 frontend files / 694 tests passed; production build passed; lint 0 errors / 31 warnings; documentation checks passed. `issue117-main-sync-all.log`. | — |
| S117-06 | Skipped | Final pushed-tree CI and human review tracked on PR #174; no approval claimed. | [#117](https://github.com/esfen14/Pinpoint/issues/117) |

## Deviations from the plan

- Main advanced 35 commits after the previous checkpoint. PR conflicts prevented
  pull-request CI from starting. An ordinary merge preserves the new escalation
  and remediation work; no workflow or published migration ancestry was changed.
- Generated schema-free merge revision `c117e6a9d042` joins both histories. The
  first harness used relative downgrade `-1`, which Alembic correctly rejected as
  ambiguous at a merge; the test now targets the explicit prior head and verifies
  that both branches remain present. No application failure was hidden.
- The browser uses real login/session APIs with in-memory ephemeral credentials;
  no API interception, saved authentication state, login trace or credential
  screenshot. Baseline snapshots are initialized from actual HARD-UP checks;
  poller acceptance and active failure/recovery timing were not repeated here.
  The preceding routed report remains their evidence.

## Follow-up

- Observe final CI and obtain human review on [PR #174](https://github.com/esfen14/Pinpoint/pull/174).
- SMTP inbox delivery and production installer deployment remain unverified.
- The separate single-attempt notification guarantee remains [#173](https://github.com/esfen14/Pinpoint/issues/173); no global retry/cache changes were made.
- Prior [routed trial](../2026-10-15-issue-117-manual-topology/REPORT.md) and
  [browser defect/retest](../2026-10-15-issue-117-live-browser/REPORT.md) remain intact.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No private addresses outside the documented target lab range
- [x] Raw evidence is referenced, not committed
