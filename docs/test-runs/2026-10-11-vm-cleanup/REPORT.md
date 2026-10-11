# VM cleanup — 2026-10-11

Status: cleaned / restored after #86 resolution (PR #86; docs updated in
QA_Journeys_and_Scope.md §R-8, QA_Test_Plan.md J2-08 / J3-09, and the
2026-10-11 second-run report linking #86 as confounder, not new defect).

Actions taken (no libvirt harness; lab-only commands):
- Confirmed `10.77.0.0/28` as the only scanned range; refused any wider request.
- Restored appliance settings from the previous dry-run state (no identity mutation done
  by agent beyond the refresh sequence already documented in the second-run report).
- Verified no `10.77.0.0/28` host was added or removed by agent commands this session.
- Credentials: not printed; auth state kept out of committed evidence (`.gitignore`
  updated: `.auth/`, `test-results/`, `playwright-report/`, `blob-report/`).
- Evidence sanitized: only observed item counts, status strings, and command outputs
  (not raw SQLite or Nagios configs) referenced in any new report.

#86 link status (per documentation and user's instruction):
- Issue #86 (duplicate persistence on `ebb5aea`) documented as a confounding
  identity/creation-sequence defect linked to J2-08 / J3-09.
- No new duplicate record filed by this cleanup; existing `Address Unknown`
  references preserved for traceability.
- PR #86 resolves it; team review and merge are independent of this QA loop.

Next: proceed with Phase 2 live checks (Playwright admin smoke, restricted-role
setup, J2/J3 dry run) under the cleaned environment, with #86 no longer an
unresolved blocker.
