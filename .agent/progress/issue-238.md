# Issue #238: Dashboard stale Nagios warning

Branch: `issue-238-nagios-stale-warning`
Status: ready-for-review

## Finish condition

- [x] Record revision and exact stopped-engine Dashboard and Service Overview behavior.
- [x] Visible warning explains stale data and stopped host/service state updates.
- [x] Verify Auto Refresh 1 minute and Manual text.
- [x] Commit sanitized separate retest evidence; preserve historical FAIL.

Requirement coverage:

| Requirement | Finish item | Proof |
|---|---|---|
| Stopped-engine prominent warning | Visible warning | Rendered regressions and reserved Docker browser/API retest |
| Service Overview frozen states | Visible warning | ServiceOverview regression and browser observation |
| Refresh text | Both modes | Settings/Dashboard tests and live retest |
| Revision and sanitized evidence | Separate report | docs/test-runs issue report and index |
| Preserve historical result | Scope exclusion | No catalog verdict edits |
| Configuration-save symptom not isolated | Scope exclusion | Not implementing unrelated save behavior |

## Plan

1. [x] Add failing UI regressions for stopped/stale Nagios warning, fresh recovery and refresh modes.
2. [x] Implement shared status-freshness interpretation and visible warnings; retain historical PID without presenting it as live proof.
3. [x] Verify focused/full frontend and docs/all gates; update owning specifications and reviewed coverage bindings.
4. [x] Deploy candidate frontend against reserved Docker API, stop/restart Nagios, verify both refresh modes and warnings, restore lab and record separate sanitized report.
5. [x] Remove scaffold and open PR, leaving CI running per user preference.

## Round log

| Round | Change | Check | Result |
|---|---|---|---|
| 0 | Read issue and source; reserved Docker lab with user approval | source inspection; supervisorctl status | Six original containers running; stored PID is treated as live forever and warning is click-only |

## State for the next session

- Last check run (exact command): docker exec pinpoint-lab-appliance-1 supervisorctl status
- Result: Nagios, Apache, nginx and Gunicorn running.
- Hypothesis: stopped polls leave a historical PID and enabled-check flags; UI must distinguish freshness from live process proof.
- Next action: inspect standalone frontend verification, then remove scaffold and open PR without CI wait.

## Decisions and notes

User explicitly reserves localhost:8000 Docker lab and authorizes stop/restart for this issue; restore it afterward. Do not run discovery or modify catalog verdicts. Stale polling alone cannot prove a stopped process; warnings must describe uncertainty honestly. Historical config-save symptom remains unisolated/outside scope.

Round 1: three stopped/stale warning regressions failed before implementation; 40 focused tests now pass, including cached-snapshot aging and fresh recovery plus both refresh-mode texts. Implemented shared frontend freshness interpretation (3-minute bound, 15-second clock) without falsely asserting stale PID proves a stopped process. Next: live retest and specs/QA bindings.

Round 2: specifications and TC-DASH-07 source bindings reviewed. Candidate Vite on5238 against unchanged appliance API, baseline /src44471f7c. Nagios stopped10:25:19Z with600s automatic-restoration guard (session55185). Original refresh5; saved1 thenManual successfully. Await actual3-minute timestamp age; full tests running.

Round 3: actual stopped/recovered browser/API retest passed; separate sanitized report added, original FAIL preserved. Nagios restarted10:29:44Z; normalpollnewPID53036/time10:31:39Z. Restoredrefresh5, loggedout, resetviewport, stoppedownedVite/removedguardfiles. Allgate final hits knownmacOS host-lock; concurrent fullfrontend saw unrelated timeoutfailures, standalone frontend run session78248 now running. Next: inspect standalone result, finish PR with CI left running.

Round 4: defaultfrontend standalone1046passed/3accountfailures; fulltwo-worker run82files/1049passed with unchangedassertions/timeouts; build/lint running in session34309. Final docs links257allresolve andcoverage239valid. User prefers no CI wait. Next: inspect build/lint and open PR.

Final local result: fullsuite1049passed with2workers; buildpassed;lint0errors/33existingwarnings. All gate remains knownmacOShost-lock failure. Report and links validate. No source change after live candidate. Remove scaffold and openPR; do notwaitCI peruser.
