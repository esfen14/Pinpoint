# Supervised TC-SS-04 recheck after timing fix (#211)

| Field | Observed run |
|---|---|
| Date / executor | 2026-10-18; Codex scripted automation with the reviewed Playwright adapter; Paeng separately authorized recovery use and explicitly started only v2 after successful recovery |
| Application tested | `299ab3ba7203c89a3ca5d8fabea42d9e5f239be2` |
| Harness tested | `724a4b55dd6983809fc2b91afb876441c4a275d8`; only authorization/progress metadata was uncommitted during execution; no product/adapter/assertion changes |
| Plan / catalog | [Module black-box catalog](../../qa/Pinpoint%20-%20Black-Box%20Test%20Cases%20by%20Module%20with%20Traceability%20Matrix.md); SHA-256 `d9374c41d7f4e5304c3475735d765ad66cb4352cc9745f76e96d78c4de0e398f` |
| Queue / set / owner | [v2 JSON](../../qa/queues/2026-10-18-issue-211-ss04-recheck-v2.json), [preview](../../qa/queues/2026-10-18-issue-211-ss04-recheck-v2.md); `issue211-ss04-recheck-v2`; Paeng |
| Immutable scope | `1a63336e7ceca199685233a85c3038bc075e6ab45ff800a51d73ffbed9c05d00`; source-current before dispatch; retained as consumed historical scope |
| Session / batch | `issue211-ss04-recheck-v2` / `issue211-ss04-recheck-v2-001`; one case, initial attempt, zero retries |
| Appliance / versions | Existing exclusive `pinpoint-qa-appliance`, UUID `351eb491-f5e1-4854-a7e4-68309ad774ad`; unchanged controlled Ubuntu 22.04/Nagios 4.5.11 preparation; installer revision unknown; upgraded existing databases |
| Baseline | Same reviewed controlled application/build/boot/master/worker/source/configuration/runtime/Staff/network/scan state; 455 source files, 2383 installed runtime files and 16 served artifacts; cached pinned image/browser checked; Staff initialized/Active/zero permissions; scheduler remains off |
| Capacity before use | Host 31 GiB disk free and about 7.5 GiB RAM available; existing VM reused, no provisioning |
| Raw evidence | Private host `/home/paeng/pinpoint-test-results/2026-10-18-issue-211-ss04-recheck-v2`; original evidence retained separately; no raw reports/auth/process output committed |
| Time zone | All timestamps below UTC; local Asia/Manila UTC+8 |

## Result

**Overall: PASS for the single supervised TC-SS-04 recheck.** The real browser
observed E1, the fixed importer accepted current-run evidence, browser logout/401
was verified, owned transport/process cleanup completed, and the supervisor
accepted the result after fresh post-case baseline proof. No product permission
failure was observed. This is the narrow accepted-result path required by
[#211](https://github.com/esfen14/Pinpoint/issues/211), not broad automation readiness.

Totals (unique TC): selected 1, attempted 1, Pass 1, Fail 0, Partial 0, Blocked 0,
Inconclusive 0, Not run 0. One batch opened and one accepted completion.
Totals (unique E2E): selected 0, attempted 0, Pass 0, Fail 0, Partial 0, Blocked 0,
Inconclusive 0, Not run 0. Historical credit: 0 accepted, 0 partial.
Recovery/preflight are setup observations, not extra case attempts.

| Case | Result | Observation | Issue |
|---|---|---|---|
| TC-SS-04 | PASS | System Status absent from sidebar; direct address redirects to Settings; fresh import, logout and independent cleanup/baseline gates succeeded | [#211](https://github.com/esfen14/Pinpoint/issues/211) |

## Expected-item observations and restoration

| Case / attempt | Expected item | Observed value | Verdict | Private evidence reference | Restoration |
|---|---|---|---|---|---|
| TC-SS-04 / 1 | E1: System Status absent from sidebar and direct address redirects to Settings | `System Status absent from sidebar; direct address redirects to Settings.`; actual Staff login, direct `/system-status` navigation, Settings URL/heading and zero matching sidebar links | PASS | `evidence/observed-TC-SS-04-E1.json`; original fixed attachment in `evidence/results.json` | `restored: true`; required logout/401, container/bridge/process cleanup and fresh unchanged baseline passed before acceptance |

The adapter/config/assertions were unchanged. One worker, one exact selected case,
one initial attempt, no setup project and no retry were used. No other prerequisite
case or historical human PASS case ran. Browser context cleanup was supported by
actual API logout and unauthenticated `/api/user/me` assertions; deleting files
was not used as session restoration evidence. Expected login/logout audit entries
remain; no account/role/setup change or audit-history deletion occurred.

## Authorized recovery and history preservation

Paeng separately approved the recovery implementation, then its actual use, and
separately explicitly started v2 conditional on successful recovery/preflight.
Authorization was recorded privately at `08:25:21.130508`.

The supported `qa_pilot.py recover` completed at `08:25:45.488446`. Under the
existing canonical host/UUID locks, it checked the prior immutable scope, original
terminal container/bridge metadata, halted session and fixed logout attachment;
queried actual daemon absence by both original container ID and name; verified
original same-user process/Unix endpoint absence; and obtained fresh supported
controlled-baseline/served-byte/image/browser proof. Proof acquisition was bounded
and the grant bound the original ledger/attempt/evidence, exact v2 scope, target,
baseline, reviewer and expiry. It imported no historical case result.

Before changing the active halt gate, it retained a private byte-for-byte archive
of the original ledger and appended one audited recovery disposition. The original
attempt remains `halted`; its result is still INCONCLUSIVE. Original session/batch
budgets and private evidence remain intact. The active gate was released only for
the named new queue. The old v4 slot was not cleared, replayed or reclassified.

At `08:28:35.459580`, a read-only ledger audit verified the original archive and
attempt prefix, unchanged original budgets, one recovery disposition and two
attempts: original halted v4 plus complete accepted v2. The current active halt
gate is false. Only v2 was permitted after recovery, and its slot is now consumed.
The [original pilot report](../2026-10-18-issue-206-ss04-pilot/REPORT.md) and all
original queue/log/catalog verdicts are unchanged.

## Fresh attempt and timing evidence

| Event / field | Observed UTC value |
|---|---|
| New journal started | `08:26:45.225618` |
| Batch / case opened | `08:26:45.226075` / `08:26:45.226760` |
| Durable new attempt consumed | `08:26:51.479064` |
| Owned container start / finish from retained daemon inspections | `08:26:51.826391372` / `08:26:53.926510217`; exit 0 |
| Playwright report start / duration | `08:26:52.550`; 1333.737 ms |
| Attempt start / selected-slot duration | `08:26:52.910`; 850 ms |
| E1 observation | `08:26:53.807` |
| Old parser's invalid derived end | `08:26:53.760`; E1 is **47 ms later** |
| Supervisor accepted result / completion | `08:26:57.264869` / `08:26:57.265015` |
| Supervised completion journal event | `08:26:57.265320` |
| Recorded case elapsed | 12.038034 seconds including supervision; not a product performance measurement |

This fresh run reproduced the same clock relationship with a 47 ms gap. The
[reviewed rule](../../qa/QA_Report_Timing.md) accepted it using independently
captured host attach launch/completion bounds and monotonic elapsed/budget, not
`startTime + duration`, import-time fallback, a grace period or altered assertions.
The retained daemon window also encloses E1. This does not identify how the
original 44 ms split among omitted slots/scheduling/possible clock adjustment.
Neither run is a validated performance measurement.

## Cleanup and durable completion

The owned container lifecycle recorded `complete`, with exit 0, removal and a
successful empty daemon absence query. Bridge cleanup joined/stopped its owned
resources, recorded `complete` and removed its socket. CLI process runners were
idle/clean. The supervisor then obtained a fresh matching host/guest/boot/process/
source/configuration/runtime/Staff/network/scan/served baseline and passed its
cleanup time budget before persisting PASS with `restored: true`.

The separate supervised start and durable UUID ledger establish the actual run;
the source journal alone is not authorization. Its serialized `status` remains
`active`, with no active case/batch, one accepted result and a
`supervised-pilot-complete` event. The durable supervised attempt is `complete`.
That journal label does not reopen the consumed slot or imply another start.

Private references: `authorization-summary.json`, `recovery-grant.json`,
`recovery/recovery-proof.json`, `recovery-verified-summary.json`, `start.json`,
`accepted-result-summary.json`, `control/session.json`, bounded probe outputs,
`control/container/container-intent.json`, retained stopped inspections and final
absence-query output, `bridge/bridge-intent.json`, and the canonical ledger/archive.
Only fixed observations, counts and reviewed timestamps are summarized here.

## Verification and limits

Before execution: `scripts/verify.sh docs` passed 193 isolated contracts;
`scripts/verify.sh frontend` passed 1003 product tests, eight offline helper checks,
types/build/lint (zero errors, 33 existing warnings). Local backend and `verify.sh all`
were omitted as the issue requires with unchanged application backend. The source
queue, exact card and missing-start rejection were checked before authorization.
Post-report docs/CI status is recorded on PR #212; a green pre-run gate is not a
claim about a later CI head.

No scan, fault, reset/restore, restart/reboot, account change, dependency install,
application deployment, diagnostic repeat or broader/unattended case occurred.
The scheduler remains disabled per the prepared baseline; reboot would invalidate
it. Other cases, broad readiness, malicious same-user isolation and memory
attestation remain outside this result. Controlled launch/build provenance and
cooperative locks remain explicit trust boundaries.

## Sanitization checklist

- [x] No passwords, tokens, cookies, keys, SNMP communities, hashes of passwords or private key paths
- [x] No target addresses outside the documented lab range
- [x] Raw auth/report/process/configuration/database evidence remains private
- [x] Original INCONCLUSIVE outcome and human results preserved; new result separately attributed
