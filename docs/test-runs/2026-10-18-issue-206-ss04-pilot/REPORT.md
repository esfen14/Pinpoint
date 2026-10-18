# First supervised automated pilot: TC-SS-04

| Field | Actual run |
|---|---|
| Date / executor | 2026-10-18; Codex scripted automation using the approved Playwright adapter; Paeng explicitly said **start** after confirming the one-case pilot |
| Application tested | `299ab3ba7203c89a3ca5d8fabea42d9e5f239be2` |
| Harness / checkout | `b50f9b11745fa919df3a8faad6d0e2762823e084`; pinned Playwright 1.64.0 |
| Installer / environment | Existing installer revision unknown; exclusive local VirtualBox `pinpoint-qa-appliance`, UUID `351eb491-f5e1-4854-a7e4-68309ad774ad`; Ubuntu 22.04, Nagios 4.5.11; upgraded existing databases |
| Catalog SHA-256 | `d9374c41d7f4e5304c3475735d765ad66cb4352cc9745f76e96d78c4de0e398f` |
| Queue / owner | [v4 JSON](../../qa/queues/2026-10-18-today-ss04-v4.json), [preview/log](../../qa/queues/2026-10-18-today-ss04-v4.md); set `today-ss04`, Paeng |
| Queue checksum | `9bcab858b917445f727dae0f49a2388a953c431fe4a330fc1d9334371fedb520` |
| Session / batch | `today-ss04-20261018` / `today-ss04-001`; one fixed case, one initial attempt, zero repeats |
| Time / zone | User start recorded 07:21:01.029461 UTC; batch opened 07:21:10.399915; durable attempt consumed 07:21:16.589307; halt recorded 07:21:19.691752; independent post-run inspection 2026-10-18T07:22:10.190520+00:00; Asia/Manila UTC+8 |
| Baseline | Exact controlled target/build, initialized Active Staff with zero permissions, scheduler off, only configured `10.77.0.0/28`; original backup retained |
| Raw evidence | Private host `/home/paeng/pinpoint-test-results/2026-10-18-today-ss04`; no raw report/auth/process evidence committed |

## Result

**Overall: INCONCLUSIVE — result-import timing failure.** The actual browser
reported one passing TC-SS-04 attempt and logout verification. The supervisor
correctly refused to accept a result when the strict parser rejected its E1
observation timing. This is tracked as harness issue
[#211](https://github.com/esfen14/Pinpoint/issues/211), not a Pinpoint permission
failure. Independent inspection supports completed resource/session cleanup and
unchanged baseline, but does not override the halted result gate.

Totals (unique TC): Pass 0, Fail 0, Partial 0, Blocked 0, Inconclusive 1, Not run 0.
Selected 1; actually attempted 1; definitive accepted case verdicts 0.
Totals (unique E2E): Pass 0, Fail 0, Partial 0, Blocked 0, Inconclusive 0, Not run 0.
Historical credit: 0 accepted, 0 partial. One batch opened; zero supervisor-accepted
batch completions. The browser/process attempt ended; the session is halted.
Original human Result fields and previous preparation reports remain unchanged.

| Case | Result | Observation | Issue |
|---|---|---|---|
| TC-SS-04 | INCONCLUSIVE | Browser assertions and logout passed; parser rejected E1 timing; supervisor halted without accepting a result | [#211](https://github.com/esfen14/Pinpoint/issues/211) |

## Expected-item evidence and cleanup

| Case / attempt | Expected item | Actual observation | Evidence assessment | Private reference | Cleanup |
|---|---|---|---|---|---|
| TC-SS-04 / 1 | E1: System Status absent from sidebar; direct address redirects to Settings | Browser PASS attachment: `System Status absent from sidebar; direct address redirects to Settings.` | Assertion observed; whole-case result remains INCONCLUSIVE because evidence timing failed import | `evidence/results.json`, attachment `TC-SS-04-E1` | Logout/401 assertion passed; independent cleanup checks below |

The exact approved UI adapter signed in as the initialized Staff user, navigated
by direct address, checked the Settings URL/heading and absent System Status link,
then logged out and asserted `/api/user/me` returned 401. One worker, one selected
case, one attempt and zero retries were recorded. No prior prerequisite case or
human PASS case was executed.

The bounded container exited 0. Its owned lifecycle recorded `complete`, removed
the full identified container and obtained a successful empty daemon absence query.
The bridge recorded `complete`, stopped its connections/thread and removed its
owned socket. The process runners completed their CLI groups. The browser report
contains exactly the fixed E1 observation and `cleanup: {session_closed: true}`.

A separate supported read-only `qa_pilot.py inspect` after the halt rechecked actual
host/guest/boot/process/source/configuration/runtime/Staff/network/scan state,
served frontend bytes and cached image/browser against the original private
baseline. It passed. This inspection started no browser/container and was not a
second attempt. The VM remains running with its scheduler disabled; no scan, fault,
account change, service restart, snapshot restore or code deployment occurred in
this run.

## Timing rejection and investigation

The parser's fixed diagnostic is `Unreviewed or stale expected-item observation`.
The actual timing fields were:

| Event | Value |
|---|---|
| Attempt `startTime` | `2026-10-18T07:21:18.069Z` |
| Reported attempt duration | 910 ms |
| Parser-computed attempt end | `2026-10-18T07:21:18.979Z` |
| E1 observation `at` | `2026-10-18T07:21:19.023Z` |
| Observation beyond computed end | 44 ms |
| Whole report start / duration | `07:21:17.708Z` / 1448.738 ms |

The case/item/verdict/text and attachment shape match the reviewed adapter. The
underlying cause of the timing discrepancy still needs pinned reporter/clock
analysis; no undocumented tolerance or altered timestamp was applied. Reported
browser duration is not asserted as an independently validated performance measure.
A read-only parser diagnostic against the same unchanged report reproduced the
rejection; it did not execute the browser, modify assertions or accept a result.

Searched open/closed issues for TC-SS-04 and Playwright report-parser symptoms;
only parent #206 matched. Filed a separate harness task #211 without the `qa-found`
product-defect label. No product requirement violation was established, and no
unsupported diagnostic repeat was run.

## Durable stop and evidence

The canonical UUID supervisor ledger retains one consumed attempt with
`status=halted`; its session/batch history was not cleared or reset. Private
`control/session.json` is halted with no accepted result; container and bridge
intents are complete. The live start was time-bound and bound to the immutable
v4 scope. Do not reuse this consumed slot, recreate its outputs or manually import
the apparent PASS to bypass the halt.

Private references:

- `authorized-start-summary.json`, `start.json`, `launcher-summary.json` and bounded launcher output.
- `evidence/results.json` (raw browser result and fixed attachments).
- `control/parser-diagnostic.json` (fixed timing rejection).
- `control/container/container-intent.json`, stopped exit-0 inspections and final successful empty absence query.
- `bridge/bridge-intent.json` plus removed socket.
- `control/post-run-inspection/inspection.json` and its read-only proof logs.

## Follow-up

1. Investigate/fix #211 in a separate preparation pass, using a sanitized fixture
   with the actual timing relationship and without weakening expected results or
   stale/foreign/cleanup evidence rejection.
2. Keep this original INCONCLUSIVE outcome and halted ledger. Any recovery/new
   attempt needs separately reviewed scope and explicit start; never reset/replay
   v4 or reclassify this run after a parser change.
3. Prepare a fresh recheck queue/card after the harness fix and reviewed recovery,
   then prove the complete supervisor result/cleanup path. Broad/unattended
   automation remains unready.

## Documentation verification

`scripts/verify.sh docs` passed (176 isolated contracts), as did documentation
links, progress structure and whitespace checks. The consumed v4 queue now
correctly rejects freshness after the known-gap inventory update; it is retained
as historical scope, never regenerated/replayed. No local
backend or unchanged frontend suite is needed; no application or harness source
was changed during execution/investigation.

## Sanitization checklist

- [x] No passwords, cookies, tokens, keys, password hashes, communities or private key paths
- [x] No target addresses outside the documented lab range; host loopback is transport only
- [x] Raw evidence remains private; only fixed sanitized observations/timestamps and issue links are committed
