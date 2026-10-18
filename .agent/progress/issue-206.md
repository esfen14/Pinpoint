# Issue #206: Module-based black-box QA readiness tooling

Branch: `issue-206-qa-readiness`
Status: in-progress

## Finish condition

- [x] Parse/validate 231 TC and 8 E2E cases, requirements, prerequisites and conflicting results.
- [x] Versioned module/person queues with explicit IDs, exclusions, batches, freshness, historical evidence and execution cards.
- [x] Enforce execution-state start/owner/scope/budgets/adapters/evidence/recovery offline; no live QA.
- [x] Inventory/link historical candidates without automatic PASS or invented provenance.
- [x] Migrate legacy validators/rendering/docs links without weakening coverage or rewriting historical outcomes.
- [x] Update reports/workflows/specs and pass isolated checks/docs gate.
- [x] Open reviewable PR with pending human decisions, adapter coverage and separately gated live work.
- [x] Implement the supervisor lifecycle core with separate start binding, cooperative UUID lock, fsynced action consumption, persistent replay/budget checks and halted failures; prove with 16 synthetic-driver contracts.
- [x] Implement and test bounded local process-group control (8 contracts) and strict private permission-report parsing (9 contracts); these components remain unwired to live execution.
- [x] Share a fixed per-user host claim between supervisor and mutating VM controllers, and collect structured host-only ownership observations; verify with local fixtures without claiming running application identity.
- [x] Implement concrete pinned-image Docker lifecycle with durable intent/consumed-transport binding and verified owned-resource cleanup (16 synthetic contracts); fix and offline-test Playwright worker reload without launching a browser (7 frontend helper checks).
- [x] Implement the owned bounded bridge with durable custody/cleanup (11 Unix-only contracts), connect container custody checks (16 container contracts), and add standalone Git/artifact/process observations (6 fixtures) that never claim verified runtime identity.
- [x] Prepare the authorized exclusive appliance: verified backup, exact deployment/build/migrations, initialized Staff, served artifacts and closed setup sessions; disclose the startup scan and temporary scheduler pause.
- [x] Integrate the narrow TC-SS-04 production driver, fixed read-only actual host/guest/served proof, controlled provenance and complete card/start CLI; pass eleven synthetic contracts and supported actual read-only inspection.
- [x] Run the first explicitly started browser/container pilot; independently verify logout/resource/baseline cleanup and report INCONCLUSIVE with harness issue #211.
- [x] Fix import timing and validate the separately authorized recovery/new-recheck/supervised PASS path through merged #212; broader/unattended readiness remains open.

| Issue requirement | Finish-condition item | Proof |
|---|---|---|
| Catalog/queues | First two items | Parser/queue isolated regression tests and real catalog check |
| Execution constraints | Third item | Offline state/adapter/budget/evidence rejection tests |
| Reuse | Fourth item | Candidate inventory, evidence validation and regression tests |
| Migration | Fifth item | Traceability/render/link validators and docs gate |
| Records and review | Last two items | Report schema, specifications, PR and CI |

## Plan

1. [x] Add shared catalog parser/tests in `scripts/qa_catalog.py`, `scripts/test_qa_catalog.py`.
2. [x] Migrate `scripts/qa_queue.py` and queue tests; add reviewed-evidence validation and historical inventory.
3. [x] Add offline execution-state/card/result validation and tests; do not launch labs or unmapped browser tests.
4. [x] Migrate traceability/rendering/tests/report templates/documentation links and specifications; verify docs.
5. [x] Review finish condition, verify required gates, checkpoint and open PR with explicit remaining live work.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 5 | Self-review added stale accepted-evidence checks (including excluded cases), normative/harness fingerprints, blocked-slot accounting, priority/module context and actual five-batch exhaustion tests | Final `scripts/verify.sh docs`; Python syntax; `git diff --check`; `scripts/verify.sh all` running | Docs green with 66 isolated checks after rejecting unknown prerequisite IDs; full local gate passes: 4310 backend/14 skips, 1003 frontend, build/lint zero errors; no live QA |
| 4 | Migrated source/derived/evidence validators and tests, fixed current/historical links, updated report templates/workflows/specs and docs gate | `scripts/verify.sh docs` | Green: all links and 61 isolated checks pass; no live operations |
| 3 | Added offline session/card/evidence validator with explicit start/owner checks, bounded batches, unchanged adapters, exact action slots and cleanup halt | `python3 -I scripts/test_qa_execute.py` | 7 tests pass; no dispatcher/subprocess exists; live preflight and recovery remain separately gated |
| 2 | Migrated module/person queue v2 and reviewer-bound evidence validation; inventoried 41 reports and attached six partial candidate mappings | `python3 -I scripts/test_qa_queue.py`; `python3 -I scripts/test_qa_evidence.py` | 8 queue and 3 evidence tests pass; no historical PASS inferred; docs migration remains round 4 |
| 1 | Added shared catalog parser with shorthand phase expansion, 239 definitions, complete procedures/expectations and result-conflict handling | `python3 -I scripts/test_qa_catalog.py`; `python3 -I scripts/qa_catalog.py` | 4 tests pass; 231 TC/8 E2E; 26 conflicts plus one free-text verdict flagged; docs gate migration remains step 4 |
| Plan | Copied approved local documentation/catalog transition into isolated issue checkout; recorded implementation plan | `gh issue view 206 --json body --jq .body` | Finish condition covers offline readiness; no live operations authorized |

## Partial-pass follow-up session (2026-10-18)

User addition: investigate partial passes so issues can be filed.

1. [x] Review all human partial verdicts, source/spec evidence and existing issues.
2. [x] File attributed acknowledgement confirmation defect [#208](https://github.com/esfen14/Pinpoint/issues/208) and missing-observation clarification [#209](https://github.com/esfen14/Pinpoint/issues/209).
3. [x] Add review-only `investigate` queues, partial-only validation, executor rejection and mandatory linked dispositions; preserve the catalog.
4. [x] Verify docs gate, selection/conflict/tampering and execution rejection checks; no live QA.
5. [x] Checkpoint/push to PR #207. Final-head CI status is recorded in the PR; inspect it before merging.

Follow-up round 1: docs gate passes with 68 isolated checks (including two new
regressions); `git diff --check` passes. ACK source corroborates the human note;
REM has no stated failing expectation and is not asserted to be a permission bug.
Prior full product checks and CI passed at `9e8d7f1`; the new-head CI must be
checked separately. Both investigation issues retain unknown original provenance
and require separately authorized live evidence where needed.

## State for the next session

- Pulled merged PR #212 at `91357da8`. #211 timing fix, audited recovery and accepted TC-SS-04 recheck are complete; report is `docs/test-runs/2026-10-18-issue-211-ss04-recheck/REPORT.md`. Actual ledger audit confirms active halt false, original halted attempt preserved, new attempt complete/PASS and one valid archived recovery disposition.
- Next action: prepare broader bounded execution support before a new assignment. The launcher is still TC-SS-04-only, and recovery's next-queue hash still restricts consumption to the already completed recheck queue. Implement a reviewed forward handoff preserving history, select new eligible case adapters/fixtures and extend only that scope, then freeze new queue/cards, recheck prerequisites and obtain its explicit start.
- Five source adapters exist; four are original human PASS, TC-SS-04 has a new attributable PASS, 234 definitions remain unmapped. Do not rerun passed cases or reset the store to create throughput. Product application remains target `299ab3b`, scheduler off; no VM or case action occurred during this pull/review.
- Post-pull local docs verification passed 193 isolated contracts plus the pinned no-browser timing worker; no local backend or unchanged frontend suite needed. The observed PR #212 ready-policy CI failure is inherited unfinished parent progress, after successful docs/tooling checks; it is not a failing parser/unit gate or a reason to erase parent progress.

## Decisions and notes

- October 15 cutoff remains provisional. Preserve catalog human verdicts; reports retain original executor attribution.
- No product code, lab access, production discovery, installer work or live test execution in this issue.
- Existing related owner changes were copied, not moved; original checkout stays untouched.
- Overall readiness plan remains `.agent/progress/ai-testing-readiness.md`; this file tracks the authorized offline implementation milestone.

- The last hardening check rejects unknown prerequisite references instead of silently ignoring them. Local full-gate product tests ran against unchanged product source; the final QA-only parser change passed the rerun docs gate.

## Readiness checklist audit (2026-10-18)

- User asked whether the entire readiness plan was complete and to check applicable items.
- Checked completed offline tasks against source, tests and reporting rules; split aggregate requirements where live enforcement/cards remain missing. The full plan is not complete.
- Refreshed stack/status descriptions and synchronized the overall plan and this progress file into the original checkout for visibility. Implementation remains in the isolated checkout.
- `scripts/verify.sh docs` and `git diff --check` pass. At pre-checkpoint head `9828931`, docs and frontend CI passed; backend was still running. New-head CI remains separate. No live tests or product changes.
- Next work: selected-case coverage/cards and evidence/ambiguity review, then live boundaries/recovery and a separately started pilot.

## Coverage/adapters implementation session (2026-10-18)

Scope: continue the approved offline readiness work; no lab connection, test launch
against an application, account setup or product behavior change.

1. [x] Add a source-bound coverage registry/validator and derived all-case matrix in `scripts/qa_coverage.py`, regression tests and `docs/qa/automation-coverage.json` / `Automation_Coverage.md`. Unknown coverage stays explicitly unmapped; partial coverage cannot become whole-case automation.
2. [x] Add reviewed source adapters for Staff permission cases (SS-04, HIS-01, RPT-07, LOG-05, PLG-07), with isolated exact-selection Playwright configuration, no setup dependencies/retries/captures, and per-item evidence. Validate registration with offline `--list`, never a browser launch. Existing human passes stay excluded by normal queue eligibility.
3. [x] Bind queue snapshots/freshness to coverage metadata and reject mismatched adapter cards; include registry checks in the docs gate, document source implementation versus live readiness, and update the overall checklist. Complete live cards still require verified prerequisites/environment and a supported reviewed launcher.
4. [x] Verify docs and relevant frontend checks, inspect CI status and checkpoint to draft PR #207; synchronize the main-checkout progress copies. Full-gate/current-head CI proof is recorded in the PR before completion.

Next action: round 1 failing coverage registry contracts, then implement validation.

Coverage round 1: five isolated coverage contracts pass; the first run failed
because `qa_coverage.py` did not exist, then the implementation passed. All 239
records currently remain unmapped until the next source-review round.
`python3 -I scripts/qa_coverage.py render --write` generated the matrix; no runtime
verdict was changed. Next action: source permission adapters and offline collection.

Coverage rounds 2–3: frontend gate passes (1003 Vitest tests, five Node selection/
Playwright-list checks, QA type check, build and lint with zero errors/33 existing
warnings). Initial exact collection found zero tests because Playwright matches
full titles; the bounded title matcher was corrected and actual collection now
proves exact selection. A Node test filename was changed to `.node.mjs` so Vitest
does not collect it as a Vitest suite; it remains explicitly required in the
frontend gate. Registry reports five source-complete/234 unmapped definitions.
Card binding rejects wrong source/mode/selection/argv; template cards remain
blocked. A new regression first demonstrated PASS without recorded actions, then
the journal was hardened to require every approved action slot.
`python3 -I scripts/test_qa_coverage.py` (7), queue (12), executor (11) pass.
`verify.sh docs` passes with 77 isolated checks.

No live browser was launched. The existing launcher does not forward the new
selection/output environment or mount its private artifacts; all actual live
cards and deployment/ownership/recovery proof remain pending.

Next action: run final local verification, checkpoint and inspect current-head CI.

Coverage checkpoint: relevant docs/frontend checks pass; full local gate and
current-head CI are running. New source tests, coverage register and guide are
committed in #207. Progress copies are synchronized into the original checkout;
implementation source remains isolated. Final green proof must be checked in
the PR rather than inferred from this checkpoint.

## Transport preparation session (2026-10-18)

User requested continuation. Inspection confirms the journal deliberately rejects
live authorization; it cannot be promoted into a dispatcher by passing environment
variables. Continue the transport portion offline, without lab or credential reads.

1. [x] Add `scripts/qa_transport.py` and isolated contracts for a queue/journal-bound transport preview: exact current case, immutable sources, unconsumed action slot, fresh offline attestations, private fresh artifact path, read-only sources and minimal credential mounts. No subprocess/live dispatch or authorization from previews.
2. [x] Add `scripts/playwright-lab --qa-preview QUEUE JOURNAL STATE_DIR BRIDGE_DIR`; reject current-case config/environment bypasses in the legacy execution path before Docker/socket/credential work. Exercise the shell entry with fake commands only.
3. [x] Wire docs-gate checks, fingerprint transport sources, update workflow/status/readiness docs and progress, verify and checkpoint to draft PR #207. Live preflight, ownership lock/deployed version proof, recovery supervisor and explicit started live cards remain pending.

Next action: failing transport validation tests, then smallest implementation.

Transport round 1: test-first run failed because `qa_transport.py` was missing.
Nine isolated transport tests now pass, including no credential file opens,
stale/modified journal/source rejection, invalid budgets/result order, used slots,
private permissions, symlink/mount delimiter rejection, retained evidence, draft
cards, offline-to-live promotion and supported shell routing. Preview creates no
socket, consumes no journal slot, writes no evidence and starts no external tool.

Transport round 2: wired docs gate/fingerprints (including bridge implementation),
updated guide/workflow/status/checklist. Read-only container/source and minimal
credential exposure are a proposed transport contract, not proved live isolation.
Live lock/deployment/recovery supervisor remains unimplemented. Shell syntax and
whitespace checks pass; relevant docs gate and final-head CI proof are maintained
in draft PR #207. Scope remains offline implementation only.

## Supervisor lifecycle session (2026-10-18)

Continue authorized implementation without contacting the lab. Existing controller
preflight and SSH/deployment helpers do not expose one proved runtime driver;
implement and test lifecycle invariants before wiring any production dispatch.

1. [x] Add `scripts/qa_supervisor.py` lifecycle core and isolated fake-driver tests: separate explicit grant, queue/journal binding, canonical private shared ledger/OS lab lock, fresh matching driver receipts and durable action consumption before driver invocation.
2. [x] Persist interrupted/running/failed-cleanup states, prevent replay/session counter resets, enforce timing/cancellation/cleanup and use existing expected-item result validation. No production driver or live CLI in this milestone.
3. [x] Add docs gate/fingerprints, document trusted-driver and cooperative-lock limits, update checklist/progress and verify/checkpoint #207. Synchronize original-checkout progress; CI proof remains in PR description.

Next action: failing lifecycle contracts using synthetic transport fixtures and
a fake driver; no real process, bridge, Docker, SSH or appliance call.

Supervisor rounds 1–2: first test-first run failed because the module was absent.
Fourteen fake-driver contracts now prove durable consume-before-run, independent
lock exclusion, wrong/expired grant rejection, matching fresh receipts, replay
across sessions, restart blocks, corrupt-state/write-failure rejection, persistent
five-batch budget, cancellation/cleanup and halt states, retained product FAIL and
rejection of unsupported prior offline results. A symlink-lock failure initially
surfaced raw OSError; the helper now rejects it with a generic validation error.
No raw driver exception text is saved. Production driver calls still need process
deadlines; measuring return time alone cannot terminate a hung callback.

User reminder: update the finish-condition checklist. Added explicit checked
lifecycle-core and unchecked production/live-proof items at the top of both
progress files; retain incomplete broader readiness conditions.

Checklist verification-note correction: the overall plan no longer labels the
later combined local run green. It retains #210's intermittent failure and
separately attributes passing stage reruns and the earlier clean baseline. This
is a documentation accuracy correction; no test/product behavior changed.

## Runtime process/result components session (2026-10-18)

Continue production-driver preparation offline. Existing deployment helpers do not
yet prove running frontend/backend identity for a target SHA; do not invent that
proof or enable a live entry. Implement concrete runtime components first.

1. [x] Add `scripts/qa_process.py` with bounded isolated process-group execution, private non-overwriting raw logs, environment control, process-tree termination/reaping and sanitized errors; test with local Python fixture processes, never VM/Docker/browser commands.
2. [x] Add `scripts/qa_results.py` strict one-case Playwright parsing: approved configuration, one non-retried attempt, attachment/item identity and private-path limits, complete PASS plus cleanup proof; unavailable/failed assertions without explicit item evidence remain inconclusive. Test synthetic reports, never acceptance runs.
3. [x] Wire docs gate/fingerprints, document supported versus pending capability, update finish conditions in both progress files, verify/checkpoint and synchronize original checkout. Runtime identity proof, driver integration and live validation remain unchecked.

Next action: failing process and report-parser contracts; no live command wiring.

Runtime rounds 1–2: both test-first modules initially failed because the modules
were absent. Eight local-process and nine synthetic-report contracts now pass.
Process fixtures cover nonzero exit, private non-overwriting raw logs, allowlist/
environment rejection, TERM-ignoring timeout, descendant termination, output cap
and uncertain-cleanup halt. The leader PID is not released before group cleanup.
Parser fixtures cover exact config/case/attempt, private inline/file attachments,
missing evidence/cleanup, failed browser as inconclusive, stale/unsafe/unreviewed
observations, duplicates and sanitized errors. Installed pinned Playwright reporter
source was inspected for JSON/attachment shape. Private umask was added so actual
future reporter files satisfy strict permission checks. No production driver
was enabled; deployment/endpoint proof and daemon/container cleanup remain open.

Runtime integration hardening: a new failing supervisor regression demonstrated
that parser `restored: false` could otherwise be ignored when the runtime driver
reported successful cleanup. The core now halts on that conflict; supervisor
contracts increase from 14 to 15, for 118 total docs-stage isolated checks.

## Shared controller and host-observation session (2026-10-18)

1. [x] Test and implement a canonical per-user host control lock shared by the supervisor and mutating `vmlab` entry points. Preserve the lock across controller subprocesses; reject forged/stale descriptors and competing owners. Only local fixture commands are permitted in verification.
2. [x] Refactor read-only VirtualBox preflight into structured observations with fresh timestamps and stable controller/process identity. This proves host ownership only; running backend/frontend, baseline and recovery remain unproved and must not become true flags.
3. [x] Update fingerprints, specifications and both finish-condition checklists; run the docs gate, checkpoint and synchronize original-checkout progress. No live execution or production driver is enabled.

Shared-control rounds 1–2: test-first modules/observation calls failed before implementation. Six local control-lock fixtures, seven new host-observation contracts and the cross-ledger supervisor regression now pass. Existing ownership-change/setup fixtures were adapted to include the real lock helper with synthetic preflight/API/SSH endpoints. No real controller, VM, browser, account or credential value was accessed. Structured observations do not satisfy live proof. Next action: finish docs verification, checkpoint and inspect exact-head CI.

Shared-control round 3: kernel start ticks are included in running observations and parsed with an isolated malformed-stat regression. Both finish-condition checklists now check the shared-host-control/structured-observation component while production driver/runtime identity/live restoration remain unchecked. Relevant docs gate passed before the final start-tick regression; final gate and exact-head CI are recorded in PR #207.

Final local shared-control check: `scripts/verify.sh docs` passes with 132 isolated
contracts; Python compilation, shell syntax, focused hardlink/forged-marker checks
and `git diff --check` pass. Checkpoint this milestone in draft PR #207 and inspect
its exact-head CI rather than carrying forward the previous head's green status.

## Same-day pilot preparation: container lifecycle (2026-10-18)

User prioritizes starting automation today, confirmed exclusive local VirtualBox
availability, then explicitly selected **Keep preparing offline** when offered
read-only preflight. Do not contact the lab. Prioritize TC-SS-04; existing human
PASS cases stay excluded. Keep the full readiness checklist truthful.

1. [x] Test and implement the concrete Docker lifecycle component around the existing bounded process helper: private durable create intent, pinned image identity, exact prepared transport, container-ID verification, bounded attach, kill/remove/absence proof and no repeat after uncertain cleanup. Exercise only fake command responses.
2. [x] Bind the helper to durable supervisor consumption, preserve private raw output, and keep real ownership/deployment/baseline/bridge proof outside this component. No CLI or default production driver may start live work.
3. [x] Wire fingerprints/docs checks, update specifications and both progress checklists, prepare a fresh blocked one-case queue after source changes, verify and checkpoint. User has not authorized preflight or case execution.

Same-day round 1: container module tests initially failed because the module was absent. Thirteen synthetic command contracts now cover pinned images, consumed-transport hashes, actual settings/mounts, initial/post-create checkpoint failures, timeout/uncertain create, foreign ownership, daemon-query failure, restart/retry rejection and non-verdict exit codes. Fixtures use unconnected local Unix sockets and fake Docker responses only.

Same-day round 2: a real synthetic Playwright IPC worker reproduced a configuration reload failure after output directory creation. The selection helper now recognizes only the pinned worker entry/IPC plus expected indices and its private artifacts; forged environment markers and initial evidence reuse still reject. The actual acceptance specs/browser were never invoked. Full local frontend gate passes: 1003 product tests, 7 helper checks, QA typecheck, build and lint with 0 errors/33 existing warnings. No human result was changed.

Verification instruction (user, 2026-10-18): skip backend test runs on subsequent
passes when application backend code is unchanged. Run focused QA tooling checks,
the docs gate and relevant frontend checks. Existing GitHub CI may still schedule
a backend job automatically; do not claim that job passed or change CI policy
without an actual result. No local backend suite is needed for this change.

Same-day round 3: full docs gate passes 145 isolated checks; full frontend gate
passes 1003 tests plus 7 helper checks, QA typecheck, build and lint (0 errors/33
existing warnings). Python syntax and whitespace checks pass. No local backend
suite ran under the user’s new verification instruction. The fresh blocked pilot
is `docs/qa/queues/2026-10-18-today-ss04-v2.json`, set `today-ss04`; the initial
unstarted draft is retained as superseded. Both finish-condition checklists and
the separate today checklist are synchronized to the original checkout after
checkpoint. Exact-head CI results are recorded in PR #207, with backend CI
automatically scheduled by the existing workflow rather than locally requested.

## Offline bridge and deployment-observation session (2026-10-18)

Current user direction: continue offline preparation, prioritize the TC-SS-04
pilot, and skip backend tests when backend application source is unchanged.

1. [x] Implement/test the owned private Unix-to-fixed-loopback bridge: consumed-slot/host-lock binding, retained lock descriptor, same-user peers, bounded time/connections/bytes/buffers, safe shutdown and durable interruption/cleanup state. Use local Unix socket-pair fixtures only; never contact the appliance origin.
2. [x] Add a read-only deployment observer/verifier that distinguishes checked source/build manifests and running process identity from Git HEAD alone. Validate with disposable file/process metadata fixtures, without SSH or live deployment claims.
3. [x] Connect bridge custody checks to the container component, update fingerprints/specifications and all finish-condition checklists, refresh the blocked pilot scope, run focused QA/docs checks (frontend only if affected), checkpoint and synchronize the original checkout. Do not enable or start live testing.

Bridge round 1: test-first bridge module was absent. Eleven real Unix-socket/pair
contracts now verify duplex/half-close/backpressure, fixed-origin custody, limits,
foreign peers, deadlines, claim loss, checkpoint failure and socket replacement.
Container contracts increase to 16, including real owned bridge plus fake Docker
and bridge loss during attach; cleanup still removes only its owned container.

Observation round 2: six disposable Git/file/proc contracts verify expected source
comes from immutable Git objects despite dirty worktrees, artifact mismatches and
untracked Python detection, unsafe path/secret exclusion, process metadata and
mid-probe changes. The standalone module disables Git network protocols/replacement
objects and does not copy process arguments/environments. It always leaves runtime/
served identity false and verified running revision null. No live proof is invented.

Bridge/observer round 3: `scripts/verify.sh docs` passes 165 isolated contracts;
Python compilation, shell syntax and whitespace checks pass. No local backend
suite or unchanged frontend gate ran, per the user’s instruction and affected
scope. Fresh blocked scope is `docs/qa/queues/2026-10-18-today-ss04-v3.json`;
v1/v2 are preserved as superseded, never started. Both finish-condition checklists
and today progress are synchronized to the original checkout after checkpoint.
PR #207 records exact-head CI; backend is automatically scheduled by existing CI,
not a requested local test or a reason to delay this helper-only pass.

## Authorized appliance preparation (2026-10-18)

User now explicitly authorizes continuing preparations by accessing the VMs.
This initially superseded the earlier offline-only preference for read-only
preflight of `today-ss04` (v3 queue). The subsequent explicit backup/deployment/Staff
approval and its completed operations are recorded below; no acceptance start was granted. Check host ownership first, hold the cooperative host
claim across guest reads, retain private raw observations and commit only sanitized
facts. Inspect actual deployed source/build/process and Staff prerequisites;
record uncertainty instead of claiming running identity from Git HEAD.

## Appliance preparation checkpoint (2026-10-18)

The user's VM-access instruction superseded offline-only preparation. They then
explicitly approved backup, deployment of `299ab3b`, dependencies/build/migrations,
application restart and disposable Staff initialization, preserving existing data.
That work is complete; acceptance execution remains separately gated. No approval
question is pending. See the [preparation report](../../docs/test-runs/2026-10-18-issue-206-pilot-preflight/REPORT.md).

- [x] Check exclusive actual UUID/controller/process/loopback endpoint ownership under the host claim; start the existing appliance without restoring a snapshot.
- [x] Take and verify consistent application/venv/configuration/database backups before deployment; retain a SHA-256-verified private host copy.
- [x] Build/deploy exact target `299ab3ba7203c89a3ca5d8fabea42d9e5f239be2`; install/check runtime dependencies, migrate both databases to `e153c4a8b2d7`, confirm integrity and active service.
- [x] Verify 123 backend app / 279 frontend source Git blobs and all 16 HTTP-served artifacts; record controlled post-deployment restart/process metadata without inventing a supervisor proof receipt.
- [x] Create/initialize disposable Staff through supported APIs with zero permissions; close and verify both setup sessions.
- [x] Disclose the automatic scan after boot (06:39:54–06:40:05 UTC) before pause; disable the serving scheduler with a temporary runtime environment override. Keep persisted configuration unchanged and record that reboot invalidates this baseline.
- [x] Record preparation evidence, index and queue log; keep TC-SS-04 Not run (0 attempts, 0 batches), preserve human verdicts.
- [x] Integrate the narrow trusted driver and fresh runtime/baseline observations; complete/review the pilot card (see the later driver checkpoint).
- [x] Obtain explicit start and independently verify browser/container/session cleanup in the first INCONCLUSIVE pilot; the result-import gap remains open.

Private evidence: `/home/paeng/pinpoint-test-results/2026-10-18-issue-206-preparation`.
Guest backup: `/var/backups/pinpoint/qa-20261018-299ab3b`. The original administrator
and five discovery devices were retained; one Staff user was added. An existing
automatic scan occurred before the consistent backup; three scan records were
retained afterwards. This is not a fresh/restored appliance or a scan-free boot.
No agent/API scan command, fault injection, snapshot restore, acceptance browser
or acceptance Docker container was launched. VM remains running with scheduler off.
Staff credentials are private in the configured controller state. The matching
administrator identity came from another saved private credential set after the
configured set returned 401; no administrator reset occurred.

Latest verification: `scripts/verify.sh docs` passed (165 isolated contracts),
v3 `today-ss04` source check passed and `git diff --check` passed. Prior head
`04f317e9` passed all CI jobs in run 39103841594; new checkpoint CI is separate.
No local backend suite or unchanged frontend suite is required; the actual target's
frontend build and dependency/migration checks passed during approved deployment.

## Narrow pilot driver checkpoint (2026-10-18)

- [x] Compose supervisor/host claim, owned bridge/container, independent bounded process/recovery runners and strict report parser for TC-SS-04 only; no implicit retry/resume or product/setup repair.
- [x] Add private reviewed controlled-deployment/build baseline, fixed read-only guest probe, actual served-byte checks and local image/browser fingerprints. Bind 455 target source files, 2383 installed runtime files, configuration, boot/process identities, Staff and scheduler/network/scan state. Standalone observer readiness remains negative; independent controlled provenance is required.
- [x] Add supported read-only `inspect` and separately start-gated `run` CLI. Validate exact source-current one-case owner/scope, baseline/image pins, private disjoint writes and separate matching expiring start before inspection/output/transport work. Use canonical per-user durable pilot ledger; halt on uncertain cleanup.
- [x] Pass eleven synthetic composed-driver/proof/gate contracts and actual supported read-only inspection; demonstrate false-start CLI denial with all reserved acceptance outputs still empty.
- [x] Prepare complete [v4 card](../../docs/qa/queues/2026-10-18-today-ss04-v4.md) and immutable JSON; v3 is superseded, never started. E1 is sidebar absence plus redirect to Settings; one initial attempt, 300-second case envelope, 30-second cleanup, exact adapter selection, no scans/faults/restarts/resets/account changes or diagnostic repeat.
- [x] Save/index the [driver preflight report](../../docs/test-runs/2026-10-18-issue-206-pilot-driver-preflight/REPORT.md), queue log and private evidence; pass `scripts/verify.sh docs` (176 isolated contracts), source/link/progress/whitespace checks. No local backend or unchanged frontend suite.
- [x] Obtain the user's explicit start for v4 `today-ss04`, Paeng; create the matching private expiring grant and run the one initial attempt (see outcome below).
- [x] Perform first TC-SS-04 attempt and publish its separate INCONCLUSIVE report; independently verify session/container/bridge/baseline cleanup, preserve halted ledger and file #211.

Actual read-only inspection uses SSH, public HTTP and Docker **image inspection**,
without starting Docker containers or browsers. Positive fresh observation fields
are not human authorization or acceptance evidence. Controlled launch/build
provenance is a reviewed trust boundary, not in-memory/kernel attestation. Existing
scheduler-off baseline, backup and automatic startup-scan disclosure remain intact.
Private baseline/inspection evidence is under the earlier preparation evidence
root's `pilot-runtime-proof/`; reserved case evidence/control/bridge paths remain
empty. Do not remove the shared lock/ledger, recreate an interrupted output path,
re-enable schedules, change assertions or bypass the launcher with manual argv.

## Authorized first pilot start (2026-10-18)

- [x] Paeng explicitly said **start** after confirming this is the single-case supervised pilot; v4 scope/owner remain unchanged.
- [x] Recheck v4 source scope and empty reserved private outputs; create the matching 15-minute private grant only after that user instruction.
- [x] Execute/inspect the first attempt; record INCONCLUSIVE and independent cleanup verification without a retry/product change (see outcome below).

Start timestamp: 2026-10-18T07:21:01.029461+00:00. Queue `today-ss04`, session `today-ss04-20261018`, batch `today-ss04-001`, exact case TC-SS-04. Report: `docs/test-runs/2026-10-18-issue-206-ss04-pilot/REPORT.md`. No other case or setup operation is authorized by this start.

## First supervised pilot outcome (2026-10-18)

- [x] Obtain Paeng's explicit start for fixed v4 `today-ss04`, TC-SS-04 only; recheck immutable scope and create the matching private expiring grant.
- [x] Run the one initial browser/container attempt; one batch opened, zero supervisor-accepted batch completions, no repeat. Browser permission/redirect/sidebar assertions and logout/401 passed.
- [x] Preserve INCONCLUSIVE overall outcome: strict import rejected E1 wall timestamp 44 ms beyond `startTime + duration`; reproduce the fixed parser diagnostic from unchanged private evidence, without another browser attempt or altered timestamps/assertions.
- [x] Verify owned container exited 0/was removed with a successful empty daemon query, bridge completed/removed its socket, and the supported independent post-run inspection matched the original baseline. Do not override the halted supervisor with these independent observations.
- [x] Search existing issues and file harness [#211](https://github.com/esfen14/Pinpoint/issues/211), without a qa-found product label. No product failure established.
- [x] Record/index [pilot report](../../docs/test-runs/2026-10-18-issue-206-ss04-pilot/REPORT.md), queue execution log and known-gap inventory; preserve original human results and earlier reports.
- [x] Complete report/checklist/index documentation gate: 176 isolated contracts, links/progress/whitespace pass; checkpoint this reporting outcome.
- [x] Complete separate #211 fix, preserve original attempt/archive/budgets, apply separately approved recovery and pass the explicitly started v2 recheck. Neither consumed queue can be replayed.

Actual application `299ab3ba7203c89a3ca5d8fabea42d9e5f239be2`; harness
`b50f9b11745fa919df3a8faad6d0e2762823e084`. Session
`today-ss04-20261018`, batch `today-ss04-001`, TC-SS-04 attempt 1.
Unique TC: attempted 1, accepted PASS 0, FAIL 0, partial 0, BLOCKED 0,
INCONCLUSIVE 1, Not run 0. E2E attempted 0; inherited credit 0.
The raw browser PASS is supporting evidence, not an accepted whole-case verdict.
The scheduler remains off and VM running; no scan/fault/setup/reset/restart occurred.
No application/harness source was edited during execution or investigation.

## Pulled #212 and reconciled accepted pilot (2026-10-18)

- [x] Fast-forward `issue-206-qa-readiness` to merge `91357da849c34aa9b2256688e331b78255ae08ba`; #212 contains the #211 timing fix, audited recovery and separately authorized successful recheck.
- [x] Review bounded attach-window timing semantics, regression/recovery contract and [accepted recheck report](../../docs/test-runs/2026-10-18-issue-211-ss04-recheck/REPORT.md). Application target remains `299ab3b`; original INCONCLUSIVE evidence is unchanged.
- [x] Read the actual canonical ledger under its existing host/UUID claim: active halt false, one preserved original halted attempt, one complete TC-SS-04 PASS, one audited recovery disposition; original archive/history passes `ready()` verification. No live state was changed in this review.
- [x] Reconcile finish checklists with the accepted supervised import/logout/container/bridge/process/baseline path. No additional browser case ran in this pull/review pass.
- [x] Complete local post-pull docs checks: 193 isolated contracts pass; the pinned no-browser Playwright timing worker test also passes. Skip local backend/unchanged product frontend suites. PR #212's observed red docs job passed the docs/tooling checks, then rejected the inherited unfinished `issue-206.md` under ready-PR policy; preserve parent progress rather than deleting unfinished work or weakening CI.
- [ ] Implement/test a reviewed next-assignment handoff: `Ledger.consume()` currently permits only the recovery disposition's exact v2 queue hash, including after that queue completes. Preserve old attempts, archives and budgets; do not clear/relocate the store to launch a new queue.
- [ ] Select the next eligible untested cases/module and implement their reviewed adapters/fixtures/assertions/cleanup. Registry has five implemented source adapters, 234 unmapped; the other four permission adapters have original human PASS, while TC-SS-04 now has accepted attributable PASS. No redundant rerun is implied.
- [ ] Expand the live executor beyond its explicit TC-SS-04-only/single-case checks for only the selected reviewed IDs and bounded batches. Existing ordinary maximum remains five cases/batch and five batches/session, not automatic permission to drain the catalog.
- [ ] Prepare a fresh source-current module/person queue/card with target/baseline/evidence paths, verify its actual prerequisites and obtain its own explicit start. Scheduler remains off; monitoring/timing/discovery fixtures need separately reviewed baseline changes.

The timing defect and accepted-pilot recheck are complete. Broader testing is
blocked by narrow supported scope/next-queue handoff and missing case adapters,
not by a remaining #211 parser failure. No further TC-SS-04 run, reset, recovery,
VM change or new test start occurred during this pull/review.
