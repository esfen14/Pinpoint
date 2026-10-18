# Pilot driver preparation and read-only inspection

| Field | Actual scope |
|---|---|
| Date / executor | 2026-10-18; Codex scripted preparation/SSH/public HTTP; Paeng authorized implementation and appliance preparation |
| Application revision | `299ab3ba7203c89a3ca5d8fabea42d9e5f239be2`; controlled deployment recorded in the [earlier preparation report](../2026-10-18-issue-206-pilot-preflight/REPORT.md) |
| Helper revision | New driver/probe under development on base `6bc0f2d2080d2b0538cd5765da5ad640e9b529ce`; exact implementation fingerprints frozen in v4 queue; no acceptance commit tested |
| Installer revision / environment | Unknown existing installer; exclusive `pinpoint-qa-appliance` UUID `351eb491-f5e1-4854-a7e4-68309ad774ad`, Ubuntu 22.04 / Nagios 4.5.11, existing upgraded databases |
| Catalog SHA-256 | `d9374c41d7f4e5304c3475735d765ad66cb4352cc9745f76e96d78c4de0e398f` |
| Queue / set / owner | [v4](../../qa/queues/2026-10-18-today-ss04-v4.md), [JSON](../../qa/queues/2026-10-18-today-ss04-v4.json); `today-ss04`, Paeng |
| Queue checksum | `9bcab858b917445f727dae0f49a2388a953c431fe4a330fc1d9334371fedb520` |
| Private baseline checksum | `da42da6cdbc38dab7ba6f9d96c2abd9cfb822123429fdd3f1e613ea50f8e07c3` |
| Latest read-only observation | 2026-10-18T07:12:20.938310+00:00 (UTC; Asia/Manila UTC+8) |
| Session / batch / attempt | Acceptance session not started; 0 batches opened/completed, 0 case attempts |
| Raw evidence | Private host directory `/home/paeng/pinpoint-test-results/2026-10-18-issue-206-preparation/pilot-runtime-proof`; never committed |

## Result

**Read-only preflight passed; acceptance Not run.** The narrow driver composes the
supervisor, owned bridge/container, bounded process runners and strict result
parser. It accepts only the fixed TC-SS-04 initial attempt after a complete
source-bound card and separately reviewed explicit start. No browser or container
was started during these checks. Actual browser/container operation and post-case
cleanup remain unverified under [#206](https://github.com/esfen14/Pinpoint/issues/206).

Totals (unique TC): Pass 0, Fail 0, Partial 0, Blocked 0, Inconclusive 0, Not run 1.
Totals (unique E2E): Pass 0, Fail 0, Partial 0, Blocked 0, Inconclusive 0, Not run 0.
Historical credit: 0 accepted, 0 partial. Preparation checks are not case attempts.

| Case | Result | Observed coverage | Follow-up |
|---|---|---|---|
| TC-SS-04 | Not run | No browser login/sidebar/direct-navigation assertion; only prerequisites and launcher guards inspected | [#206](https://github.com/esfen14/Pinpoint/issues/206) |

## Observed preparation checks

1. Fixed read-only guest probe compares 455 source files against immutable target
   Git objects and the separately recorded target build. It reads no password
   hashes and imports no serving application. All source/build matches passed.
2. Fresh host UUID/controller/VM start identities and loopback forwarding match the
   controlled preparation. Guest boot, master/worker identities, source/config file
   stamps, 2383 installed runtime code/resource files, interpreter identities,
   database versions, initialized permission-free Staff, scheduler-off state,
   configured `10.77.0.0/28` and the three existing scan records remain unchanged.
3. Actual HTTP-served public bytes match all 16 target frontend artifacts. Local
   Docker image inspection confirms the approved image; cached Playwright headless
   Chromium revision 1248 and its binary fingerprint match. Neither is launched.
4. The supported `qa_pilot.py inspect` command completed successfully and persisted
   a private receipt carrying `live_authorized=false` and `test_cases_executed=0`.
5. The private start template has `explicit_start=false` and an expired timestamp.
   The actual run CLI rejects it. Case evidence/control/bridge directories remain
   empty: no session, action consumption, bridge or container was created.
6. Eleven isolated driver contracts cover consume-before-run integration, held claim,
   scope/replay rejection, drift and controlled launch/build checks, missing-start
   denial before outputs, hard-link-safe dependency fingerprinting, and mandatory
   session/container/bridge/process cleanup. All resources/observers are synthetic;
   these fixtures do not contact the appliance, Docker or a browser.

The independent reviewed record ties this baseline to the previously authorized
stopped-service deployment, exact-target build, migrations and subsequent controlled
restart. Positive composed inspection depends on that provenance plus fresh actual
checks. It is not derived by changing the standalone observer's negative readiness
flags, and it is not a kernel/in-memory attestation or proof of human consent.

## Preparation corrections and limits

The initial dependency probe rejected installed package-cache hard links. A separate
bounded runtime inventory now hashes canonical regular dependency files, includes
link counts/stable metadata, rejects symlinks and detects changed bytes. The public
source observer's strict single-link rule remains unchanged.

The standalone observer uses an extra one-second margin for process/source ordering,
which was inconclusive for this closely timed deployment. Its flags remain false.
The new probe separately verifies all source/config/runtime input change times
precede a conservative lower bound on the recorded process start, and binds current
unchanged stamps/identities to the independent controlled launch record. Timestamp
ordering alone never creates launch provenance.

The first queue-preview script used an unavailable helper name; it was corrected
before publishing v4. An attempted CLI call without the resulting start file also
rejected before execution; the subsequent explicit-false-template rejection is
separate evidence of the actual start gate.

Only the permission pilot is supported. No scans, fault injection, account changes,
service restart, scheduler change or VM restore occurred in this pass. The scheduler
remains off as recorded in the earlier report; reboot or process/input drift blocks
this baseline. Missing browser cleanup evidence halts even if resources were removed.
No automatic retry/resume or diagnostic repeat is authorized by this card. Assertion/
browser failures without explicit failed-item evidence remain INCONCLUSIVE, not an
invented product FAIL or an automatically filed finding.

## Expected-item evidence and cleanup

| Case / attempt | Item | Observation | Verdict | Cleanup |
|---|---|---|---|---|
| TC-SS-04 / 0 | E1 | Sidebar and redirect behavior not observed | Not run | No acceptance session/resources created |

Private references: `baseline.json`, `capture-3.stdout`,
`cli-inspection-v3/inspection.json` and its bounded probe/image logs. The earlier
backup, account-setup evidence and automatic startup-scan disclosure remain in the
original preparation report; no old report verdict is rewritten.

## Follow-up

Show the v4 card and obtain a separate explicit start for `today-ss04`, owner Paeng,
one initial TC-SS-04 attempt, private output paths and written session/resource
cleanup. Only after that actual user response may a matching expiring affirmative
start record be created. Preserve human catalog verdicts and record acceptance in a
new report. Runtime/cleanup validation and broader readiness checkboxes stay open.

## Verification

`scripts/verify.sh docs` passed (176 isolated contracts); source-current v4 queue,
whitespace and progress checks passed. No local
backend suite or unchanged frontend suite was run; no product source changed.

## Sanitization checklist

- [x] No passwords, tokens, keys, password hashes, SNMP communities or private key paths
- [x] No target addresses outside the documented lab network; host loopback is transport only
- [x] Raw probe/process/auth evidence remains outside Git; only sanitized observations are committed
