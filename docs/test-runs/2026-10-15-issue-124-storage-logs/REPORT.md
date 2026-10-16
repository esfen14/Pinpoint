# Test run: issue-124-storage-logs

| | |
|---|---|
| Date | 2026-10-15 |
| Commit tested | Application fresh `f80d6c1f`; upgrade/API/browser `5f0a7ef8`; installer `ffb4cc3c` |
| Plan | [Issue 124 / plan issue 11](../../issues/issue-011.md) sections E–H |
| Tester | Codex |
| Environment | Exclusive linked VM clone `pinpoint-issue124-appliance`, Ubuntu 22.04.5, Nagios 4.5.11; fresh SQLite databases followed by a populated upgrade; dedicated internal network and loopback SSH/web endpoints; no target scans |
| Raw evidence | Task laptop: `/tmp/issue124-evidence/`; private credentials are separately retained outside the repository and never included in evidence |

## Result

**Overall: Partial.** All scoped storage/log/retention behavior and four live
browser journeys pass. The full upgrade retains administrator settings. An
unrelated installer healthcheck mode mismatch remains open as installer #9.
The first full application gate also encountered a timing-dependent unchanged
BandwidthCard test; its exact retest passes. The final local `scripts/verify.sh all` rerun is green (3,315 backend passed,
14 skipped; 696 frontend passed, build/lint green with 31 warnings). CI status is
recorded in the PR; reviewer approvals and installer ISO boot remain outside
this run's evidence.

Totals: Pass 16, Fail 1, Blocked 0, Skipped 1.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| INST-01 Fresh install | Pass | Separate base-snapshot clone with paired installer; healthcheck 60 pass / zero fail before first-run setup; `vm-fresh.log` | [#124](https://github.com/esfen14/Pinpoint/issues/124) |
| INST-02 Journal volume | Pass | New drop-in has SystemMaxUse=100M and MaxRetentionSec=7day; journald active. About 192 MB input gives 84.5 MiB usage, then 92.5 MiB (97,009,664 allocated bytes) after rotation, below the target; `journal-volume.log` | #124 |
| INST-03 Real installer-log rotation | Pass | Actual logrotate forced twice: active file truncated, latest .1 archive retained, older .2.gz compressed; `installer-live.log` | #124 |
| INST-04 Repeat policy application | Pass | Two runs retain custom journal policy byte for byte and remove only exact installer defaults; edited managed file also retained; `installer-live.log` | #124 |
| INST-05 Full upgrade | Pass | Installer deploy upgrades app f80d6c1f → 5f0a7ef8; both admin journal files SHA256 unchanged; service/API and UI work afterward; `vm-upgrade.log` | #124 |
| STORE-01 Isolated helper/API cases | Pass | Temp-file sizes, nested totals, no symlink double count, missing paths, scan budget and unreadable folder, status without monitoring plugins; `backend-focused.log` (72 total focused tests) | #124 |
| STORE-02 Live storage | Pass | Both actual database sizes nonzero, per-location disk space, missing database-backup folder and archive size returned by service-user API; `live-api.log` | #124 |
| LOG-01 Isolated tail/security | Pass | Small/large/unterminated logs, end-read byte/line caps, newest-last, after filtering, command/output redaction, unreadable/symlink/FIFO handling, fixed path and validation; `backend-focused.log` | #124 |
| LOG-02 Live log and validation | Pass | Actual configured Nagios log read as application service user, nonempty sanitized lines inside caps; bad bounds/path/duplicate parameters rejected; `live-api.log` | #124 |
| AUTH-01 Live API roles | Pass | Anonymous status/log calls 401. Reader lacks both (403); dashboard-only and logs-only accounts receive only their permitted response; `live-api.log` | #124 |
| UI-01 Admin storage and refresh | Pass | Actual browser shows both DBs, free disk and threshold help; Nagios tab loads latest log and refresh gets 200; audit category/filter still works; `browser.log` | #124 |
| UI-02 Dashboard-only | Pass | Browser renders storage despite unrelated Network Health 403; hides System Logs navigation; `browser.log` | #124 |
| UI-03 Logs-only | Pass | Browser reads Nagios log and hides Dashboard navigation; `browser.log` | #124 |
| UI-04 Restricted reader | Pass | Browser hides both elements/navigation and guards direct page URLs; `browser.log` | #124 |
| REG-01 UI states and existing regression | Pass | 28 focused frontend tests: low-space warning, partial/unavailable totals, loading/empty/error/403/retry, permission hiding, independent status and unchanged DashboardPage tests; unchanged backend dashboard suite also passes; `frontend-focused-final.log`, `backend-focused.log` | #124 |
| REG-02 Final full gate | Pass | `scripts/verify.sh all`: 3,315 backend passed / 14 skipped; all 696 frontend tests passed, build and lint passed (31 warnings); docs report verification also green; `all-final.log`, `docs-report.log` | #124 |
| UPG-HEALTH Existing mode mismatch | Fail | Post-setup/upgrade healthcheck: 59 pass, one fail; expects hosts.cfg 664, unchanged application writer uses 640. Nagios validation and read/reload checks pass. No mode was widened; `upgrade-health.log` | [installer #9](https://github.com/lorraine-pangilinan/PinPoint-Installer/issues/9) |
| ISO-01 Installer ISO boot | Skipped | Executed the installer's actual deployment/privilege modules against its base VM; did not rebuild/boot the interactive ISO. Does not claim ISO packaging validation. | #124 |

## Deviations from the plan

- The installer was located in its separate repository. Changes are in
  [installer PR #8](https://github.com/lorraine-pangilinan/PinPoint-Installer/pull/8)
  via an existing fork because upstream push access was denied.
- Used an exclusively owned clone with a separate internal network, avoiding
  mutations of the shared QA appliance and targets. The first SSH attempt used
  an older lab key; the rebuilt-base key was then used successfully.
- The existing `setup-admin` credential-label mismatch (#167) was avoided by
  completing first-run setup through the supported login/complete-setup API.
- Browser tests ran in a no-network container with a Unix-socket bridge to the
  exclusive loopback endpoint, using the committed opt-in `issue-124-live`
  Playwright project. No auth screenshots, traces or videos were recorded.
- The first `scripts/verify.sh all` run: 3,315 backend passed / 14 skipped;
  frontend 695 passed / one unchanged BandwidthCard callback timing failure.
  The exact unchanged BandwidthCard module retested 19/19 green. No test was
  weakened and no unrelated source was edited.

## Follow-up

- Keep paired application/installer PRs unmerged until CI and required human
  reviews are satisfied. The healthcheck contract follow-up is installer #9.
- Interactive installer ISO boot/packaging requires its release workflow; this
  VM run covers actual fresh deployment and upgrade module execution.
- Journald's limit is host-wide, rotates whole files and can temporarily exceed
  a target with an active journal; the test observed values at the stated points,
  not an absolute hard quota or seven days of elapsed retention.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
