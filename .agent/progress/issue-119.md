# Issue #119: System Refinement Add Flap Detection Settings, Flapping Filter and Flap History

Branch: `issue-119-flap-detection-settings`
Status: in-progress
<!-- Status is one of: in-progress | blocked | ready-for-review -->

Plan issue #6. Depends on #123 (plan #10): this branch is stacked on its commit 5d0b5dd6 (unmerged, unpushed when this branch was cut).

## Finish condition

- [ ] 6.1 With default settings, generated host and service definitions are unchanged.
- [ ] 6.1 Custom thresholds write low_flap_threshold/high_flap_threshold; invalid values return 400.
- [ ] 6.1 Flap detection off writes flap_detection_enabled 0; a rejected config rolls back with 422.
- [ ] 6.1 Flapping endpoint returns the right items for seeded history; only allowed windows (400 otherwise).
- [ ] 6.1 Response reports when global flap detection is disabled.
- [ ] 6.2 settings.system user can enable/disable/set thresholds and sees them after reload.
- [ ] 6.2 Invalid thresholds blocked with a message; a 422 shows Nagios's message.
- [ ] 6.2 "Flapping only" filter lists exactly the flapping items.
- [ ] 6.2 Drawer lists flap history for the window; empty state when none.
- [ ] 6.2 Existing dashboard and drawer tests pass unchanged.
- [ ] Deliverables: migration with downgrade, tests, specs + Implementation_Status, help text on card, `scripts/verify.sh all`.

Requirement coverage:

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Settings fields + migration, defaults unchanged | items 1-3 | test_create_host_cfg, migration test |
| PUT /api/system accepts fields, 400/422 | items 2-3 | test_settings_permissions |
| GET flapping endpoint, windows, global-off flag | items 4-5 | test_network_health_activity |
| Settings card, validation | items 6-7 | SystemSettingsConflict.test.tsx |
| Flapping-only filter (services + hosts) | item 8 | table tests |
| Flap history in drawer | item 9 | StatusDetailDrawer.test.tsx |
| Spec files + help text | deliverables | verify.sh docs |
| Lab report in docs/test-runs (section F) | NOT done: lab is off limits unless asked; left to a person | - |
| Out of scope: nagios.cfg globals | - | - |

## Plan

1. [ ] Model + migration: SystemSettings Flap_Detection_Enabled (true), Flap_Low_Threshold, Flap_High_Threshold (nullable floats); extend to_dict. Files: server/app/system_models.py, new migration, server/tests/unit/test_flap_migration.py
2. [ ] Templates: host.cfg.tpl, service.cfg.tpl, host_config_templates.py render flap lines only when non-default. Test: server/tests/unit/test_create_host_cfg.py
3. [ ] PUT /api/system: validate (0-100, low<high, both-or-neither?), apply via regenerate, 422 rollback. Files: server/app/api/system/settings.py, test_settings_permissions.py
4. [ ] GET /system/network-health/flapping?hours= with global_flap_detection_enabled. Files: network_health_activity.py, test_network_health_activity.py
5. [ ] Frontend types/context + Flap detection card. Files: client/src/types/settings.tsx, SystemSettingsContext.tsx, SystemSettings.tsx, SystemSettingsConflict.test.tsx
6. [ ] Flapping-only filters. Files: ServiceStatusTable.tsx, HostTable.tsx + tests
7. [ ] Flap history in StatusDetailDrawer + types + test
8. [ ] Specs + Implementation_Status; verify.sh all; delete progress file; PR.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | plan written | - | - |

## State for the next session

- Last check run (exact command): none yet
- Result: -
- Hypothesis: follow the #10 commit (5d0b5dd6) as the pattern
- Next action: step 1, write failing migration/model test then model+migration

## Decisions and notes

- Branch stacked on unmerged #10 commit; PR for #119 must merge after #123's PR (or include it).
- `gh pr create` unavailable? gh works now (checked 2026-10-14).
