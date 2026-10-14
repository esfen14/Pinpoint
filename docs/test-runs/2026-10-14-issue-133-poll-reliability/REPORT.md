# Test run: issue-133-poll-reliability

| | |
|---|---|
| Date | 2026-10-14 |
| Commit tested | Application source synced from issue branch `4dd006e3` to existing VM; on-disk VM Git HEAD remains `1ca2c757` (matched source/build hashes in [earlier run](../2026-10-14-issue-133-live/REPORT.md)). Harness/progress branch `30bd3676` before this report. |
| Plan | Issue #133 §G; `.agent/progress/issue-133.md` step 9; not an ISO QA queue |
| Tester | OpenCode agent |
| Environment | Existing appliance VM and isolated demo targets on `10.77.0.0/28`, preserved DB. No reset, new deployment, or induced Nagios CGI outage. |
| Raw evidence | Terminal count summaries in this session; database and login responses were not dumped or committed. |

## Result

**Overall: Partial.** A real, reversible SSH service fault kept its acknowledgement across two scheduled polling intervals and, on recovery, removed it with exactly one new AUTO_RESOLVED record. The bounded script was interrupted by tool timeout after recovery and before printing its final repeat count; a separate read-only query afterward found the same count. This supports idempotence over the elapsed post-recovery period but is not a load/performance benchmark.

Totals: Pass 3, Fail 0, Blocked 0, Skipped 2.

## Cases

| Case | Result | Notes | Issue |
|---|---|---|---|
| Still-failing acknowledgement retention | Pass | Baseline target `dev-28829a / ssh-22-tcp`: active ack 0, AUTO_RESOLVED count 1. Broke only web01 SSH, observed CRITICAL alert, acknowledged (HTTP 201). After 145 s (at least two 60-s scheduler intervals), alert remained CRITICAL and acknowledged; counts were active 1, AUTO_RESOLVED 1. | — |
| Recovery auto-resolution | Pass | Restored web01 SSH in guaranteed cleanup; after recovery, acknowledgement vanished and counts were active 0, AUTO_RESOLVED 2. Later API reported the service OK. | — |
| Repeated-poll idempotence | Pass | Separate read-only database query after the bounded script exceeded its tool timeout showed active 0, AUTO_RESOLVED 2 (no additional row). The appliance and scheduler stayed running during the elapsed time. Does not prove behavior over an extended soak. | — |
| Failed/empty Nagios poll preservation | Skipped | No real CGI outage induced; isolated `server/tests/unit/test_status.py` is the evidence. | — |
| Performance/load target | Skipped | Only one service acknowledgement and normal polling cadence were observed; no latency, scale, or resource measurements. | — |

## Deviations from the plan

The command reached the after-recovery count but exceeded its 750-second tool timeout before its final print. This is an execution harness timeout, not an observed product timeout. The target restoration in `finally` completed before timeout; `scripts/vmlab targets up`, a second `scripts/vmlab targets fix web01 ssh`, and an authenticated status check afterward confirmed web01 running and service OK. No database content beyond counts was logged. The original preserved VM database was not reset.

## Follow-up

- No new product defect confirmed. Backend-dependent History gaps remain #141–#144.
- Reviewer approval and current-head CI are still outstanding; this limited run does not establish full performance or failed-CGI behavior.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is summarized without raw API/database output
