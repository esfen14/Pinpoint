# Issue #259: real NCPA forecast label selection

| Field | Value |
|---|---|
| Date / zone | 2026-10-19, Asia/Manila (UTC+8) |
| Executed candidate | `b4afa8a0176cbc2d78a53fe4dbba29eb3f18334c` (forecast implementation and regressions); subsequent changes are documentation only |
| Appliance baseline | Existing reserved Docker lab; mounted source revision `44471f7cc5ee94348cff18015993dd023d53365d`; no candidate application source deployed |
| Executor / mode | Codex; scripted official agent/Nagios/polling checks and offline candidate forecast execution |
| Plan | [#259](https://github.com/esfen14/Pinpoint/issues/259), canonical label consumer follow-up from #242/#256 |
| Agent | Official NCPA3.5.0 amd64 DEB on owned Ubuntu22.04 container, emulated on ARM64; official v3.5.0 client through protected-token adapter |
| Network | Reserved internal Docker lab10.78.0.0/24; fixture agent10.78.0.20, no published agent port |
| Fixture | Unique `issue259-agent`; generated memory/disk descriptions; `pinpoint_nd_ncpa` command identity; notifications disabled; no discovery or production inventory edits |
| Candidate execution | SQLite online-backup copy of real history; separate empty application database; scheduler off. No timestamp/value/label rewriting and no writes to the live forecast table |
| Raw evidence | Private git-ignored `test-results/issue-259/` contains actual history copy, public baseline source and sanitized `result.json`; no raw database committed |
| Catalog credit | Issue-specific regression/consumer verification; zero catalog TC/E2E cases executed or credited |

## Result

**Pass for canonical real-history selection and preserved insufficient-history
behavior.** The official agent's memory/disk checks returned OK. Real Nagios checks
and normal application polling stored short labels. The unchanged old selector
produced no forecast rows; the candidate selected both series and correctly stored
`insufficient`, with one hourly sample each and no crossing date.

This is not a live positive forecast or disk-fill prediction comparison: history
spans minutes, not the required half of a72-hour window. Long, rising controlled
regressions prove numeric forecasts separately. Real history was not aged,
synthesized or filled to manufacture a crossing.

## Observations

| Check | Result | Actual observation |
|---|---|---|
| Direct official memory check | Pass | `OK: Percent was30.10%`, perf label `'percent'`, thresholds80/95 |
| Direct official disk check | Pass | `OK: Used_percent was0.80%`, perf label `'used_percent'`, thresholds80/95 |
| Stored memory history | Pass | `ncpa-memory-5693-tcp`, command `pinpoint_nd_ncpa`, metric `'percent'`,3 samples,18:47:31–18:49:35 Manila,29.4–29.9% |
| Stored disk history | Pass | `ncpa-disk_root-5693-tcp`, same command, metric `'used_percent'`,2 samples,18:48:35–18:49:35 Manila,0.8% |
| Baseline job on the copy | Confirmed defect |0 forecasts and0 stored rows: labels excluded before insufficient assessment |
| Candidate job on same real history | Pass |0 forecasts and2 stored rows: both `insufficient`, raw metric strings retained, hourly Sample_Count1 each, Crossing_At null |
| Numeric label regressions | Pass | Short, quoted and full-path memory/disk series yield warning80, latest61.3%, slope0.3 points/hour, R²1 and expected crossing within0.02h. Controlled72-hour data, not live measurements |
| Canonical exclusions and bounds | Pass | Other plugins, swap, disk I/O, CPU and ambiguous short identities excluded; invalid series cannot consume the cap; invalid snapshots of the same tuple cannot contaminate hourly values/thresholds |
| Existing safety contracts | Pass | Forecast fit/job/route/migration target71 tests passed; fixed mixed-row statement count5, exact selected tuples, caps, rotation, commit-failure retry, sample/coverage and fit rejection rules retained |

## Attempts and limits

An early readiness copy had only one disk sample; it already selected both
insufficient series, but collection continued until both resources had multiple
normal polls. Initial fixture validation had a no-default-contact warning and the
disk path needed quoting in the temporary check command; both were corrected
before final history capture. Final validation had zero warnings/errors. A first
reload attempt used a missing PID-file location; the observed Supervisor PID was
then used. No application command-generation behavior was changed.

The job reuses the exact chart/summary classifier as a deterministic connection-local
SQLite function. Both the series-list and hourly queries apply it before limits
and aggregation, preserving the fixed query count and raw series identity. No
schema, migration, dependency, threshold, fitting, notification, scheduler or
history-ingestion change was made. An existing mixed-row cost fixture now explicitly
identifies its intended NCPA plugin rather than relying on metric text alone;
its counts/query assertions are unchanged.

Local full verification is reported in the PR. The all gate stops at existing
macOS QA supervisor host-lock checks. Linux CI is left running per the user's
preference. No installer/systemd, production deployment, independent hardware,
scale benchmark, browser or72-hour real trend/threshold crossing is claimed.

## Restoration

- Original Nagios configuration restored under an exact-content guard and
  validated. Original SHA-256 restored:
  `f7ac7cd621c9f84df849c270ed9a7022470145b389807b18f2cf89802e8fe85c`.
- Reloaded the original configuration and verified fixture absent from active
  status before removing only its service/host performance and status rows.
  No unrelated history, inventory or audit records were deleted.
- Removed only verified owned agent container
  `906ff62262e62e659193a8ef18458361aca3bf24d14c20ecd14615a8d4aba7de`
  (label `pinpoint.issue=259`) and protected temporary runtime directory.
- All six original containers remain running; Nagios running. Application source
  and live forecast consumer were not replaced. Candidate writes were limited to
  isolated copied/local databases. Sanitized evidence retains counts/labels/time
  ranges without credentials.
