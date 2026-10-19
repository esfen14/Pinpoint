# Issue #259: NCPA forecast short labels

Branch: `issue-259-ncpa-forecast-labels`
Status: in-progress

## Finish condition

- [ ] Canonical NCPA virtual-memory/disk short labels and full paths eligible.
- [ ] Swap, disk I/O, other plugins and ambiguous short identities excluded.
- [ ] Counts, coverage, thresholds, cap/rotation, empty/insufficient and safety rules preserved.
- [ ] Numeric regressions and suitable real-history verification with revision/report.

Requirement coverage:

| Requirement | Finish item | Proof |
|---|---|---|
| Short and full labels | Canonical selection | Parameterized numeric job regressions |
| Resource/plugin exclusions | Exclusions | Negative identities, cap starvation and mixed snapshot tests |
| Safety unchanged | Existing contracts | Entire forecast fit/job/route/migration tests, query/cursor/count checks |
| Real history/revision | Separate report | Official NCPA normal polling history, isolated copy job; live crossing not claimed without sufficient duration |

## Plan

1. [x] Add failing numeric label/exclusion/cap/aggregation regressions in test_forecast_job.py.
2. [x] Reuse ncpa_resource_dimension in both SQL selection and hourly fetch, before cap/aggregation, through a connection-local SQLite scalar function; no DB migration or data rewrite. Verify focused forecast suites.
3. [x] Collect actual memory/disk samples in reserved Docker lab, run candidate on isolated SQLite copies and restore fixture changes; document revision/result and history-duration limits.
4. [ ] Update owning specs/report, run backend/docs/all gates; remove scaffold and open PR without waiting CI.

## Round log

| Round | Change | Check | Result |
|---|---|---|---|
| 0 | Read issue and forecast/classifier/tests; lab reserved by user | source inspection | Existing SQL label filter excludes short labels and does not verify plugin identity |

## State for the next session

- Last check run (exact command): git status --short
- Result: clean before plan.
- Hypothesis: connection-local SQLite function reuses exact canonical Python classifier without unbounded Python candidate fetch or post-limit filtering.
- Next action: write failing forecast-job numeric/exclusion regressions.

## Decisions and notes

User reserves localhost8000 Docker lab for real sample collection and isolated-copy forecast verification; restore afterward. No migration, new dependency, history rewrite, notifications, engine config behavior or forecast math change. New real history demonstrates insufficient state; seeded long history proves numeric forecast arithmetic. Do not age or fake real samples to imply live eligibility. No CI wait per user preference.

Round1: 13 regressions failed before classifier reuse; forecast fit/job/route/migration suites now71passed. Existing generic test-cost snapshots now explicitly identify NCPA, preserving their intended mixed-row/count assertions. Official NCPA3.5.0 agent real memory30.1/disk0.8 checksOK; normal Nagios fixture loaded with zero validation errors, polling collection underway.

Round2: official agent normal history memory3/disk2samples; baseline0rows vs candidate2insufficient rows on exact SQLite copy. Counts/labels/times preserved, no live positive crossing claimed. Original Nagios cfg hash restored, inactive fixture history/owned agent/protectedfiles removed; six originals running. Report/specs updated. Fullbackend stage session43879 running; allgate fails knownmacOShost-lock. Next: inspect fullbackend result and openPR withoutCIwait.

Round3: merged main#238 frontend/docs only, retained both report/index entries; allforecast suites rerun71passed aftermerge. Docs258linksresolve, coverage239valid. Fullbackend stage passed70% with no failures sofar; pendingcompletion.
