# Issue #238: stopped Nagios Dashboard retest

| Field | Value |
|---|---|
| Date / zone | 2026-10-19, Asia/Manila (UTC+8) |
| Candidate frontend revision | `d062def92652a7248c38ad401a7a4c5692abd4e8` |
| Appliance | Existing reserved six-container Docker lab; mounted source `/src` revision `44471f7cc5ee94348cff18015993dd023d53365d`; no appliance source deployment |
| API dashboard.py SHA-256 | `d984eecb2f6ad5a86680ef211b842117b659ec158b0cc58390b9b8a332374d32` before/after |
| Execution | Codex; AI-assisted actual browser, scripted Supervisor/API observations; issue-specific functional retest |
| Reference | [#238](https://github.com/esfen14/Pinpoint/issues/238), TC-DASH-06 / REQ-DASH-05 |
| Catalog SHA-256 | `fa02ed4dc5de4260c0234804a3daa15d2bbae955d1123f6fd59415d91cdfce25` |
| Queue / session | Issue-specific reserved Docker session; no catalog queue/card imported or credited |
| Served candidate | Vite at localhost:5238 against real localhost:8000 API; candidate frontend only, explicitly composite deployment |
| Private raw evidence | Git-ignored `test-results/issue-238/`: sanitized running/stopped/recovered API snapshots; browser accessibility observations in task tool record |

## Result

**Pass for the scoped functional requirements of #238.** Both required refresh
texts were observed after saving through Settings. Real Nagios was stopped and
restarted; the Dashboard and desktop Service Overview visibly warned about stale
data and frozen states. Fresh normal polling cleared both warnings after restart.

This is a separate adapted Docker retest, not a replacement for the catalog's
historical human FAIL. Zero catalog TC or E2E cases are credited: the literal
systemd appliance procedure was adapted to Docker Supervisor, and installer/VM
behavior was not tested. No historical result, tester attribution or date is
rewritten.

Initial one-minute text verification used frontend `1affd3ea` before the final
warning-copy sentence was added. Final stopped/Manual/recovery observations used
`d062def9`; the refresh implementation was unchanged between those revisions.

## Exact observations

| Step | Result | Observation |
|---|---|---|
| Initial running baseline | Pass | Six original containers running. Supervisor Nagios PID30. API returned `running=true`, PID30, `last_status_update=2026-10-19T10:24:38.780704+00:00`; original refresh preference 5 minutes |
| Save Auto Refresh - 1 minute | Pass | Settings displayed Saved; Overview header read `Auto-refreshing every 1 min` |
| Stop actual Nagios | Pass | `supervisorctl stop nagios` at 18:25:19 Manila (10:25:19Z). Automatic restoration guard armed before waiting; no config changes or fake history injected |
| Save Manual while stopped | Pass | Settings displayed Saved; Overview header read `Auto-refresh: Manual`. This is a personal display preference, not the unisolated Nagios-configuration-save symptom |
| Old API snapshot during stop | Confirmed root cause | API retained PID30, `running=true`, enabled host/service switches and exactly the old 10:24:38 timestamp. The recorded PID was not live process proof |
| Age/reload observation | Pass | Candidate showed warning once recorded status was at least 3 minutes old; actual final-page observation at about 18:28 Manila showed `Data Updated 4 min ago`, `Monitoring unavailable` at top and `Nagios 4.5.11 Status unavailable` in Service Overview |
| Prominent warning, no expansion | Pass | Both top of Dashboard and Service Overview displayed: “Nagios is not reporting current status. Displayed data may be stale.” Then: “While stopped, Nagios is not checking hosts or services. Host and service states will not change while Nagios is stopped. Check the monitoring engine and its status polling.” No row expansion was needed |
| Desktop visibility | Pass | Browser viewport temporarily set to1440×1000 using documented viewport control so the existing desktop-only Service Overview was visible. The top warning is also present independently of that panel |
| Restart and normal ingestion | Pass | Guard restarted Nagios at18:29:44 Manila (10:29:44Z); Supervisor PID53036. Normal polling stored `last_status_update=2026-10-19T10:31:39.066371+00:00`, PID53036, start10:29:42Z |
| Recovery UI | Pass | After returning to Overview with fresh real API data: header `Online`, `Auto-refreshing every 5 min`; Service Overview `Nagios 4.5.11 Running`, `Data Updated Just now`. Both warnings absent |

## Source identity

Candidate SHA-256:

- DashboardPage.tsx: `1f16b3e8a9c1ce15d5382ac39cb7cfbb269c5dd2984f5e34c0f3eaa6ee425111`
- ServiceOverview.tsx: `c0624b563cdefef2c3c6428543cf931fc9d93d2244547855c28f51c75f9d7ddd`
- NagiosWarning.tsx: `f06bd5ccb2bcb3b59325272064dbcbaeed057c0b4aa7e38255f9d40f3bf966cf`
- useNagiosStatus.ts: `066b2d49039edd38a71e85f88886ae85f3ea3cd3d39f125771a7539a3b00016c`

## Attempts and verification limits

Three focused regressions failed before the implementation. Final focused target
passed40 tests, including stopped/stale warnings, cached age changes in Manual
mode, fresh recovery and saved refresh text. Full verification results are recorded
in the PR. An initial full frontend run had an unrelated BandwidthCard chart
assertion failure; it was retained and the unchanged full suite rerun. That concurrent repeat produced additional timeouts
across unrelated screens under local load; a standalone final frontend run was
then started with the temporary browser server stopped. The first
all-gate attempt also overlapped a warning-copy/fingerprint update and rejected
that transient source mismatch; the stable final tree was verified again.

The browser connector had a navigation wait timeout although navigation completed;
subsequent state reads and native accessibility actions verified the actual pages.
An initial Vite process retained an older warning module; restarting the owned
server and opening a fresh browser tab verified the final exact wording above.
Screenshot file writes were denied by the browser tool (`EPERM`), so no saved PNG
is claimed. Sanitized exact API fields and accessibility observations are retained
here and in the tool record instead. No secrets, raw logs, cookies or databases are
committed.

The API's `running` flag remains a historical snapshot field. Frontend freshness
is not an authoritative operating-system process probe and cannot distinguish a
stopped engine from failed polling. It deliberately says status is unavailable.
There is a three-minute grace period plus up to15 seconds before a cached snapshot
is flagged. Installer/systemd behavior, independent hardware, and the historical
Nagios-configuration-save symptom remain unverified.

## Restoration

- Actual Nagios restarted and normal polling/recovered API timestamp verified.
- Original personal refresh preference5 restored via Settings; Saved and recovered
  Dashboard header visibly confirmed.
- Supported Account menu → Log out → Sign Out returned the browser to Login.
- Temporary viewport override reset. Owned Vite process and temporary guard/probe
  files are removed after the run; no user-owned server is stopped.
- Appliance backend/configuration files were not replaced; dashboard.py hash
  unchanged. All six original containers remain running. No fixture inventory,
  history or user data was deleted; normal audit/poll history remains.
