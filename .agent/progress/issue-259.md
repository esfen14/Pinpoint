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

1. [ ] Add failing numeric label/exclusion/cap/aggregation regressions in test_forecast_job.py.
2. [ ] Reuse ncpa_resource_dimension in both SQL selection and hourly fetch, before cap/aggregation, through a connection-local SQLite scalar function; no DB migration or data rewrite. Verify focused forecast suites.
3. [ ] Collect actual memory/disk samples in reserved Docker lab, run candidate on isolated SQLite copies and restore fixture changes; document revision/result and history-duration limits.
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
