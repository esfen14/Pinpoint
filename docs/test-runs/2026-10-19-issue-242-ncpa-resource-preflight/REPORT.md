# Test run: issue-242-ncpa-resource-preflight

| | |
|---|---|
| Date | 2026-10-19 (Asia/Manila) |
| Candidate tested in isolated API tests | `c895709cdb587640f5f36b92aa8ff3340ba996c5` |
| Plan | [Issue #242](https://github.com/esfen14/Pinpoint/issues/242) |
| Tester / mode | Codex; scripted real-agent preflight and isolated pytest; no manual QA-case result |
| Catalog / queue | Not a catalog case execution; issue-specific diagnostic preflight only |
| Appliance baseline | Existing ARM64 Docker lab, `/src` Git revision `44471f7cc5ee94348cff18015993dd023d53365d`; deployed network_health.py SHA-256 `78382323db309d6cb89c3bd0e53cfe192f2be7972ec4512dc5acca3aa5df8bbf` matches pre-fix origin/main source |
| Candidate deployment | Not deployed: the agent preflight exposed a separate label mismatch before any application or Nagios configuration change |
| Environment | Reserved existing Docker appliance and five targets; isolated internal `10.78.0.0/24`; temporary x86-64 Ubuntu 22.04 agent with official NCPA 3.5.0 DEB and official tagged v3.5.0 check_ncpa.py |
| Evidence | Sanitized agent check observations below; downloaded public package/client under git-ignored `test-results/issue-242/`; local focused output `/tmp/pinpoint-242-green.log` |

## Result

**Overall: Blocked for live chart acceptance.** The selector fix passes 57 focused
Network Health tests, including 17 new regression variants. The reserved appliance
has no NCPA service history and its trends API returns `ncpa: null`. Real-agent
fixture checks then exposed [#256](https://github.com/esfen14/Pinpoint/issues/256):
short NCPA labels do not match the resource dimension predicates. The issue's
required working-agent/stored-history/browser acceptance cannot be credited to the
selector correction alone. No live chart PASS or new catalog verdict is claimed.

## Observations

| Diagnostic | Result | Observed evidence | Issue |
|---|---|---|---|
| Existing lab baseline | Pass for preflight | Authenticated trends request HTTP 200, `ncpa: null`; history has no NCPA services, no check_ncpa plugin file/inventory | |
| Official NCPA CPU check | Pass for agent connectivity | `cpu/percent`, aggregate=avg: OK, `'percent'=6.00%` | |
| Official NCPA memory check | Pass for agent connectivity | `memory/virtual/percent`: OK, `'percent'=31.60%` | |
| Official NCPA disk check | Pass for agent connectivity | `disk/logical/\|/used_percent`: OK, `'used_percent'=0.80%` | |
| Resource dimension mapping | Blocked | Current ingestion preserves these labels; CPU/memory predicates require the dimension word as well as percent, disk requires disk and percent. This is source inspection after observing real agent labels, not a live chart failure | [#256](https://github.com/esfen14/Pinpoint/issues/256) |
| Dashboard Average Resource Utilization | Not run / blocked | No candidate deployed or real resource history polled into appliance; no deployed-page acceptance result | [#256](https://github.com/esfen14/Pinpoint/issues/256) |
| Network Health Average Resource | Not run / blocked | Same prerequisite gap; neither populated nor empty live UI credited | [#256](https://github.com/esfen14/Pinpoint/issues/256) |

## Restoration

No application source, Nagios configuration, resource history or inventory records, target services,
scan settings or plugin state were changed. API sign-in was followed by logout;
normal authentication audit entries remain. The temporary owned agent and its
protected runtime fixture files are removed during cleanup; final cleanup result
is recorded below before checkpointing. Existing lab containers are preserved.

## Scope decision

The work-issue procedure requires stopping a thread when its fix needs behavior
not named by the issue. The additional label mapping and any resource-summary or
forecast impact are recorded in #256 for a human scope decision. The #242
selector fix is independently reviewable; live acceptance remains unchecked.

Cleanup verified: owned fixture container absent; the original six containers remain.
Deployed source and original hosts.cfg hashes still match the preflight baseline.
