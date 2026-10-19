# Current-case adapter preparation

## 2026-10-19 Edit Account dependency review (#219)

Codex reviewed the current written cases, assertions, fixtures and cleanup for
TC-ACC-09, TC-SS-04, TC-HIS-01, TC-PLG-07, TC-NCPA-08, TC-RPT-07, TC-LOG-05,
TC-ROL-04, TC-ACC-08 and TC-ACC-10 against the Edit Account reuse guard. The
permission cases exercise navigation and GET denials; TC-ACC-08 reads the alert
column and Add User checkbox; TC-ACC-10 creates new inactive accounts and its
cleanup edits omit passwords. None submits an existing password through Edit
Account. Their assertions, prerequisites, observations and cleanup remain valid.
The added account-page unit test covers the reuse error and corrected retry;
existing Add User assertions are unchanged. Only these reviewed dependency
fingerprints were refreshed in `automation-coverage.json`. Coverage status,
expected-item mappings, catalog verdicts and execution permissions are unchanged.
This is source review, not a live QA result; existing queues/cards still need
normal freshness checks and separate live authorization.

## 2026-10-19 sidebar dependency review (#231)

Codex reviewed the sidebar-only reorder against the written cases and assertions
for TC-ACC-09, TC-ROL-04, TC-SS-04, TC-HIS-01, TC-PLG-07, TC-NCPA-08,
TC-RPT-07 and TC-LOG-05. The seven permission adapters assert exact hidden
links and redirects (plus API denial where required); TC-ROL-04 expects only
Overview and Settings. All three reordered links remain gated by the same
permission, and labels, routes, filtering, setup and cleanup are unchanged.
Their Sidebar.tsx dependency fingerprints were refreshed after that review.
Coverage statuses, case results and execution permissions are unchanged; changed
source still requires new queue scope and current live prerequisites before use.
The rendered-sidebar unit regressions verify the new order and denied visibility;
no live QA case was executed for this change.

## 2026-10-19 consolidated catalog results

Modules 13–15 now link their recorded runs; Modules 22–23 and E2E carry the
historical results from the previous catalog. TC-LOG-04 and TC-SET-05 carry the
lab owner's manual PASS confirmation. Compared with `44471f7c`, case titles,
priorities, requirements, dependencies and safety classification are unchanged.
TC-LOG-04 alone clarifies its procedure and explicitly checks restoration; its
coverage remains unmapped. Other procedures and expected items are unchanged.
The register fingerprints were refreshed with this comparison recorded in
`catalog_consolidation_review`. Adapter source hashes, expected-item mappings,
coverage decisions and execution permissions are preserved. Existing queues and
cards remain subject to freshness checks. No automation was run or authorized
by this consolidation.


## 2026-10-19 result-only catalog refresh

The Modules 1–11 verdict updates changed the catalog's exact hashes. A comparison
against `43f0df103752d485f4cab786ee29ce6a5e049add` verified unchanged case behavior,
requirements, prerequisites and safety classification after masking result fields.
The coverage register's catalog/case fingerprints were refreshed; adapter source
hashes, coverage statuses, expected-item assertions and execution permissions were
preserved. The dated comparison is recorded in the register's
`catalog_result_review` field. This is not a new automation run or authorization
to resume an older queue. Existing immutable queues and cards still require their
normal freshness checks against the updated catalog and register.


[Automation coverage](Automation_Coverage.md) accounts for all 231 TC cases and
eight E2E scenarios. It is generated from `automation-coverage.json` and shows
source implementation, expected items still missing and unassigned executors.
It does not change the human catalog or certify any runtime PASS.

Seven permission adapters are source-complete: TC-SS-04, TC-HIS-01, TC-RPT-07,
TC-LOG-05, TC-PLG-07, TC-ACC-09 and TC-NCPA-08. Eight additional source-only
module adapters are under issue #214 for TC-ACC-08, TC-ROL-04, TC-DI-02,
TC-DI-03, TC-DI-07, TC-DI-08, TC-HIS-04 and TC-DASH-07. TC-DI-07 has source coverage but stays outside
the live allowlist while the uppercase expectation mismatch and failure-report
handling are unresolved. TC-ACC-10 has partial source coverage for E1/E2.
The next proposed untested batch
is TC-ACC-09 followed by TC-NCPA-08; each uses the existing initialized Staff
account with zero permissions. TC-ACC-09 has separate E1 page-denial and E2 API-403
evidence; missing either cannot yield PASS. TC-SS-04 already has an attributable
accepted supervised PASS. The other four original adapters have human PASS and
remain excluded from default pending queues. Across all 239 cases/scenarios, 15
have source-complete adapters, one is partial and 223 remain unmapped. Source coverage does not authorize the next batch or imply runtime
acceptance; its cards, current prerequisite observations, reviewed ledger handoff and explicit
start remain separate requirements. The launcher now implements a fixed serial
batch for only TC-SS-04, TC-ACC-09 and TC-NCPA-08; see the
[next batch review](Next_Permission_Batch_Review.md).

## What is implemented

- `scripts/qa_coverage.py` validates the complete register, catalog/case hashes,
  source-file hashes, review metadata, adapter identity and expected-item markers.
  Implemented means every expected item has source-reviewed assertion coverage;
  markers do not prove that assertions are correct or that a browser ran.
- Queue snapshots include the case's coverage record and fingerprint the register,
  selection configuration and helper. Preparing/checking a supplied execution card
  rejects unmapped/partial coverage and a changed mapping, adapter, title, project,
  config or exact argv. Changed sources require renewed review and new queue scope.
- `client/playwright.qa.config.ts` selects only `qa-permissions.lab.spec.ts` in
  `qa-permissions`, with explicit current IDs, one worker, no retries or setup
  dependencies, fixed loopback origin and disabled trace/video/screenshot capture.
  A failed test stops further tests; bounded action/navigation/case/global limits apply.
- The issue #214 module config selects only explicit IDs from
  `qa-modules-2-9.lab.spec.ts`; direct legacy launcher dispatch rejects this
config. The supervised `qa_pilot.py run` path now accepts only seven complete
  read-only mappings from this config, after reviewed cards, fresh baseline proof
  and a separate explicit start. It has one partial TC-ACC-10 mapping (E1/E2 only). TC-ACC-10 creates
  inactive users with alerts disabled, but the rows persist and E3 would require
  an unapproved no-active-role state; its card must remain blocked. The seven complete
  mappings require exact approved credentials and pre-existing fixture inputs; they
  do not create accounts, roles, devices, or port state. Of 31 target cases, 24
  remain outside the live allowlist: TC-ACC-10 is partial, TC-DI-07 is blocked on
  its source/result mismatch, and 22 remain unmapped.
- Each adapter signs in through the UI using an already initialized disposable
  Staff account, checks its role, zero permissions and completed password/setup
  state, then checks the exact hidden sidebar link and redirect. API cases open
  the specified API address in the browser and assert 403. No intercepted response
  or shell operation replaces a case step. Sanitized E1 evidence is attached only
  after all its assertions succeed. Logout and unauthenticated `/me` checks record
  cleanup; Playwright disposes the independent context. Login/logout audit entries
  are expected side effects and must not be erased.
- `client/qa/selection.mjs` requires explicit supported unique IDs and a new, empty,
  same-owner private directory (0700 recommended), rejecting symlinks and broader
  permissions. JSON/artifacts stay there. It does not inspect credentials or a lab.
- The offline journal requires complete expected-item observations, every approved
  action slot recorded, timeout compliance and verified cleanup before PASS.
  Recording an action is an attestation, not dispatch or proof of execution.

## Preparation commands

These commands read local sources and produce metadata; none launches Playwright,
contacts the appliance, provisions an account or runs a product case:

```bash
python3 -I scripts/qa_coverage.py check
python3 -I scripts/qa_coverage.py show --id TC-SS-04
python3 -I scripts/qa_coverage.py card-template --id TC-SS-04
python3 -I scripts/qa_coverage.py render --write
```

The template includes exact source identity and command selection. It deliberately
has BLOCKED readiness, no reviewer/observed prerequisites, no evidence path and no
timeouts, with `human_required: true`. It cannot open a case. Never fill those fields
with guessed observations or simply switch the blocking flag to make it execute.

To review or change coverage, inspect the full written case and relevant behavioral
specification, every assertion and fixture/cleanup step. Record reviewer/date,
procedure coverage, each E1/E2 observation method and all relevant source hashes.
A partial adapter remains partial. If the catalog or a dependency changes, review
the impact before refreshing hashes; regeneration alone is not a coverage review.

## Remaining live requirements

The isolated runner now has an **offline preview entry point**. For a queue with
an opened offline case, complete reviewed source-bound card and fresh synthetic
or independently obtained offline attestations, use:

```bash
scripts/playwright-lab --qa-preview QUEUE_JSON JOURNAL_JSON PRIVATE_STATE_DIR PRIVATE_BRIDGE_DIR
```

This prints JSON only. `scripts/qa_transport.py` checks queue/journal identity,
source freshness, owner, fixed batch order/budget, completed prior slots, fresh
offline preflight attestations and an unconsumed initial action before preparing
one current-case container plan. It does not read credential values, consume the
action slot, create directories/sockets, contact the lab or execute the plan.
Missing cards or observations block the preview; do not invent them to get output.

The proposed transport passes exactly that case ID and `/evidence` into the new
config, mounts source read-only, mounts only the two needed Staff credential files
read-only, and reserves a separate writable evidence mount. It uses network none,
read-only container root, dropped capabilities, no-new-privileges and temporary
scratch space. Existing evidence is never overwritten. State/evidence/bridge paths
must be disjoint from each other and the checkout, same-owner, private and free
of symlinks or Docker mount delimiters; evidence and bridge directories must be
empty. Only credential file metadata is inspected, never its values. Runtime
image/browser availability, compatibility and private evidence retention still
need proof; the container image uses the existing tag, not a digest pin.

The preview explicitly returns `live_authorized: false` and BLOCKED readiness.
The legacy launch path rejects `playwright.qa.config` arguments and current-case
environment variables before reading private state or invoking socket/Docker tools.
It cannot execute a preview. Do not run the printed Docker argv by hand or work
around this gate with a host browser. Argument checks are fail-closed routing for
this supported entry point, not a sandbox against arbitrary shell access or an
agent writing another config.

A future live supervisor must hold the exclusive lab lock, prove actual runtime
ownership, deployed revision and restoration baseline, durably consume the action
slot before launch, enforce cancellation/timeout and halt on unresolved recovery.
It must then revalidate unchanged scope/files, create the private origin bridge,
execute only the approved selection and persist result/cleanup evidence. An offline
journal's attestation cannot substitute for these checks. Preview metadata may
contain local private paths; keep it outside committed evidence.

The reviewed TC-SS-04 card is the narrow exception described below. Account readiness, target revision, lab claim,
preflight, output lifetime, interruption/recovery and set start must be reviewed and
proved. Browser hooks may fail because a fixture is unavailable; that is not proof
of a product permission defect. E1 alone cannot pass a case if cleanup failed.
Other modules need their own assertion/fixture/recovery mappings; these permission
checks do not establish discovery, NCPA, report content, performance or E2E coverage.

## Verification

`scripts/verify.sh docs` checks the registry/derived view and isolated Python
contracts. `scripts/verify.sh frontend` type-checks both configs/adapters and runs
`node --test qa/selection.node.mjs` and
`node --test qa/module-selection.node.mjs` before existing frontend checks. Nine
additional Python transport tests use synthetic private files and exercise the
preview/legacy rejection paths without external commands. The Node tests use
Playwright `--list` with no browser or credentials: they verify exact explicit-ID
collection, no setup dependencies/retries and rejected invalid selections/private
paths. They are harness checks, not live acceptance evidence.

## Supervisor lifecycle core

`scripts/qa_supervisor.py` provides an importable core with no default driver.
The narrow `qa_pilot.py` caller is described below. Isolated core tests supply a synthetic driver;
none of these tests accesses Docker, SSH, sockets, a browser or an appliance.

The core requires a separate reviewed `supervised live` start grant bound to queue
hash, owner, set, session, target revision, canonical lab UUID and expiry. An offline
journal remains offline: the core neither changes its authorization mode nor
mutates it. A future application of a grant must still correspond to an actual
human-approved start. The grant structure is an identity/expiry check, not a signed
authorization system or proof of human consent.

Every checkout must share one private canonical ledger directory for the lab.
Under an exclusive nonblocking OS lock for its UUID, the core revalidates scope,
paths and fresh driver receipts twice before consuming an action. Receipts must
match UUID, loopback origin and target revision and affirm runtime identity,
exclusive use, clean deployment, baseline and recovery. Their acquisition is the
trusted driver's responsibility; passing booleans does not establish real proof.
Any prior result in the offline source journal must match the durable supervised
result for that exact queue/set/case; offline results alone cannot skip execution.

The private ledger uses atomic replacement and file/directory fsync. A case is
persisted as running **before** the driver is invoked. Case replay is rejected even
under a new session; five-batch counters persist per queue/set/owner/session. A
running entry after restart blocks further dispatch. Corrupt state, unsafe file
permissions, symlink/hardlink files and incomplete checkpoints fail closed. No
implicit reset, recovery clearing, diagnostic repeat or next-case substitution is
implemented. A validated restored product FAIL is retained as FAIL; lifecycle
completion does not mean the product passed.

The trusted driver interface consists of `verify(plan)`, `run(plan, remaining)`,
`cancel(plan)` and `cleanup(plan)`. The core checks remaining case time, passes the
budget to the driver, measures returned elapsed time, invokes cancellation after
exceptions/timeouts/interruption, and always attempts cleanup. Successful cleanup
requires a fresh matching receipt within the step budget; result evidence then
passes the existing per-expected-item validator. Unresolved run/cleanup/proof or
malformed result leaves a durable lab halt with a generic reason, not exception
text that may expose credentials. Sanitizing assertion observations remains the
trusted result-parser/driver's responsibility.

This does not yet enforce production subprocess timeouts: a trusted driver must
bound each call and terminate its entire process group/container before reporting
cancellation/cleanup success. A blocking Python callback cannot be forcibly stopped
by these elapsed-time checks. Mutating `vmlab` commands now share the canonical
host control lock described below; direct controllers and other users do not.
Connecting actual deployed-version/endpoint proof, baseline and
restoration checks, private raw output parsing and crash recovery requires the
production integration work still unchecked in the readiness plan. No default
ledger directory is created and no supported CLI can call a live driver yet.

## Runtime process and result components

`qa_process.py` implements bounded Linux/POSIX process-group execution for a future
trusted driver. It has no CLI or default executable. The caller supplies an explicit
canonical executable allowlist and reviewed argv; no shell expansion or inherited
credential environment is used. Only PATH/HOME/LANG/LC_ALL may be passed. This is
not an argument/target authorization layer or filesystem/network sandbox.

Each run has fresh, private, non-overwriting stdout/stderr files, a monotonic
deadline and an aggregate output-size limit. Timeout/interruption/excess output
triggers TERM then KILL as needed for the owned group. The leader PID remains
reserved until cleanup, the direct child is reaped and executable group descendants
must be gone. An uncertain cleanup halts the runner instead of silently resetting
it. Raw output is retained privately; exceptions and returned summaries contain no
raw command output. Local Python child fixtures test these behaviors; no Docker,
SSH, browser or appliance process is invoked by the tests.

This helper cannot terminate a daemon-owned Docker container merely by killing
its CLI, or a child deliberately escaping the process group. The production driver
still needs container-ID tracking, kill/remove/inspect checks or an appropriate
cgroup boundary. Adopted zombie descendants await their parent/init reaper; only
the direct child is reaped by this helper. A missing/ambiguous process identity
fails closed. Existing controller locking and real runtime ownership checks are
still separate requirements.

`qa_results.py` parses only the seven reviewed permission adapters. It validates
pinned Playwright version/configuration, one project/case/initial attempt, no
retries/captures, fixed origin, consistent totals/status/timestamps and exact
expected-item/cleanup attachment identities. The actual owned attach launch/completion UTC and monotonic elapsed time must
be supplied independently, within the consumed case budget. Playwright selected-slot
duration does not define a wall end; no timing grace is added. A stale report cannot
certify a new run. See [timing rule and investigation](QA_Report_Timing.md). JSON duplicate
keys, unsafe/private-path violations and oversized or unreviewed evidence reject.
The prepared container bootstrap sets `umask 077` so reporter/artifact files meet
private-file requirements.

Inline base64 JSON and private `/evidence` attachment paths are supported. The
parser copies only reviewed fixed observation text and validated timestamps into
new private item files; arbitrary errors, logs, diagnostics or page text are not
copied. Existing sanitized evidence is never overwritten. PASS requires the
successful attempt, every expected item and `session_closed: true` cleanup evidence.
The supervisor rejects explicit parser `restored: false` even when a driver
claims successful cleanup. It still needs independent runtime/cleanup proof; an attachment alone
does not establish restoration.

The current adapters emit PASS items only. A browser/tool failure without explicit
failed expected-item evidence is INCONCLUSIVE, never an invented product FAIL.
Missing cleanup remains `restored: false` and must halt supervision. Importing
structured product failures will need reviewed adapter changes and their own
regressions. Thirteen synthetic-report tests validate parsing; they are not runtime
acceptance results.

These components are now wired through the narrow pilot entry below. Their
isolated tests do not prove actual browser/container execution or post-case
session/baseline cleanup; those remain pending the explicitly started pilot.

## Shared host controller claim and structured observations

`qa_control.py` serializes the supervisor and mutating `scripts/vmlab` commands
through `/tmp/pinpoint-qa-control-<uid>/controller.lock`. The directory/file must
be private, owned by the current user, canonical and free of symlinks; the file
must have one hard link. The store is fixed across checkouts and independent of
HOME, TMPDIR, VM state directory and ledger settings. It conservatively serializes
all cooperating labs for that user. Never delete or replace a held lock/store.
Private ledger directories must still be shared for persistent replay/budget
history; the host claim prevents concurrent execution across differing ledgers,
but cannot reconstruct their separate histories.

Mutating controller entries acquire the lock before reading configuration and
before preflight/SSH/API/VM work. Nested calls carry an inherited descriptor to
the same held kernel lock. A PID/environment marker alone, closed descriptor,
unheld open descriptor or descriptor to another file cannot bypass the claim.
Nested calls close their duplicate without releasing their ancestor's flock.
A future driver must explicitly forward `Ledger.control_fd` through `pass_fds`
and `PINPOINT_QA_CONTROL_FD` when calling this controller while supervision owns
the claim. This is not yet wired to any production driver.

The lock is cooperative within the same host `/tmp` and user namespace. Direct
VBoxManage, `demo/demo_lab.py`, legacy browser launchers, another user/namespace,
or privileged/manual file replacement can bypass it. It is not a sandbox, access
permission or sufficient unattended-readiness proof. Read-only status/preflight
commands do not take this claim; structured observations alone do not claim
exclusive use for a future run.

`scripts/vmlab preflight --json` returns a structured read-only host observation:
canonical appliance UUID, state, controller/VM PIDs, loopback origin/SSH port and
UTC observation time. Preflight rechecks VM UUID/state/session and process
inventory; running process observations include kernel start ticks
to reject PID reuse and bind later observations. Missing/changed metadata or ambiguous endpoint ownership
rejects. Each VBoxManage read has a 20-second timeout; a future driver must also
enforce its total deadline and hold the host claim across proof/run/cleanup.

The observation distinguishes powered-off state from proved running endpoints,
sets `live_authorized: false`, and provides no target revision, running frontend/
backend identity, clean deployment, baseline or restoration claim. It cannot pass
the supervisor's live proof check. Deployment `Git HEAD` and a successful sync
still do not prove what Gunicorn or the web server serves.

Six local lock/controller fixtures, seven new structured-observation contracts and
the supervisor's cross-ledger exclusion regression run without VirtualBox, SSH,
HTTP, Docker, browsers or a real account. Existing setup fixtures copy the lock
helper into their disposable fixture checkout; they do not set up a live account.

## Pilot container lifecycle and worker loading

`qa_container.py` provides the concrete Docker lifecycle component for a future
trusted driver. It has no CLI/default driver and is not permission to execute
preview commands. Before any daemon operation it requires the held canonical
host/UUID claim and the matching durable running attempt, including a digest of
the entire consumed transport. The execution card's `container_image_id` must pin
an approved `sha256:<64 hex>` image ID; the supplied image must match the prepared
plan. Mutable tags alone cannot execute. Case/cleanup budgets cannot exceed the
consumed plan, and elapsed time since consumption reduces the remaining budget.

Private control output must be separate from source, credentials, bridge and
evidence. The private socket must belong to an active owned bridge; the container
component verifies its custody before creation, before attach and after attach.
The concrete bridge component is described below; connecting both components to
the production supervisor and collecting actual deployment proof remain pending.
The case evidence root must still be empty. Two independent bounded process
runners share the private control-output directory so recovery can run when the
attach runner has halted. Child commands now use `umask 077`, including Docker's
CID file; raw logs and intent remain private and never become report prose.

The component fsyncs a unique create intent before Docker create, pins the image,
sets an explicit Bash entrypoint and records the actual full container ID. It
checks ID/name/ownership token, image/user/command, no-network/read-only/capability/
privilege/restart settings and every bind mount before attach. After bounded
attach it requires a stopped container and consistent CLI/container exit code.
It returns process metadata, never a product PASS/FAIL. Expected-item parsing and
actual application/session restoration remain separate requirements.

Cleanup identifies only its own resource, kills it if running, removes it and
requires a successful daemon query proving absence. Docker CLI exit or a failed
inspect/list query is not absence proof. A failed create is looked up by the
durably recorded unique name, but the attempt still halts even when no resource
is visible because a delayed daemon operation could finish later. Ownership or
isolation drift, failed checkpoints, uncertain cleanup and interruption halt;
existing control output/intent prevents an implicit restart or retry. Cleanup
cannot clear the supervisor's halted ledger or claim the baseline is restored.

Sixteen synthetic command-response contracts exercise these paths. Local Unix
sockets are disposable metadata fixtures with no upstream. No Docker daemon,
container, browser, SSH endpoint, account or appliance is used by those tests.
One integration fixture uses the real owned bridge with synthetic Docker commands
and asserts that no upstream connection occurs.

A synthetic Playwright worker exposed an adapter preparation defect: Playwright
creates its artifact directory before its IPC worker reloads the configuration,
so unconditional empty-root validation rejected the real worker. Selection now
permits only the private owned `artifacts` directory for the pinned Playwright
worker entry with an actual IPC channel and expected worker indices. Environment
markers alone cannot relax the guard. Initial configuration and the container
lifecycle still reject reused evidence. The frontend gate has seven offline
selection/collection/worker checks; the worker fixture requests no page/browser,
imports no acceptance spec and produces no current-case result.

The initial TC-SS-04 pilot was inconclusive and the separately started #211
recheck passed. The next prepared scope contains TC-ACC-09 and TC-NCPA-08 only,
using the same controlled target and Staff state after fresh read-only checks.
No new case runs until its separate reviewed handoff and explicit start.

## Owned bridge and read-only deployment observations

`qa_bridge.py` provides the private Unix-socket relay for the future trusted driver.
It has no CLI or automatic start. It requires the matching durable consumed
transport and held host/UUID claim, and retains its own duplicate of the host-lock
descriptor until shutdown. The socket path, fixed `127.0.0.1:18080` upstream,
connection/byte limits and time budget bind to that transport. Production accepts
only same-user Unix peers. User-namespace mappings that cannot satisfy this check
remain blocked; do not relax the peer guard at execution time.

The standard plan permits at most 16 concurrent connections and 32 MiB total
bidirectional traffic, with 64 KiB buffers in each direction and a one-second
maximum origin-connect timeout bounded further by the remaining case budget.
The relay handles partial writes, backpressure and half-close without recording
request bytes, cookies, credentials or response content. Normal disconnects close
that connection; lost scope/socket custody, foreign peers, origin-connect failure,
exhausted limits and deadlines halt the bridge. Socket identity/mode/owner and
the consumed ledger entry are rechecked throughout the relay.

Private fsynced intent precedes bind. Stop joins the owned thread, closes its
connections/listener, removes only the matching socket and checkpoints complete
or halted state before releasing the retained lock. Existing intent blocks implicit
reuse; socket replacement is left intact and never certified as cleanup. A future
driver must stop the container before disposing the bridge, require successful
cleanup for both, and retain its enclosing supervisor claim through actual baseline
verification. Neither component alone proves session or appliance restoration.
Eleven local Unix-socket/pair contracts include large duplex transfer, half-close,
limits, foreign peers, claim loss, failed persistence and socket replacement. No
appliance TCP, Docker, SSH or browser is used.

`qa_deployment.py` is a standalone standard-library read-only observation module,
with no SSH, service restart, network request or live CLI. Local preparation reads
source hashes from the specified full Git revision's objects, independent of dirty
working files, plus reviewed frontend artifact hashes. Git subprocesses have a
restricted environment, disabled replacement objects/lazy fetch and denied network
protocols. A reviewed build hash is still not proof of that build's provenance.

The observer checks regular canonical public source/build files, required
entrypoints, SHA-256 hashes, size limits, unexpected Python files and stable
file/inventory metadata. Hidden secret stores, environment files, virtualenvs and
tests are outside its source inventory. It does not read process environments.
Candidate Gunicorn processes under the application server directory have PID,
parent/start identity and command hashes rechecked; command arguments are never
copied. Start-time ordering is a conservative observation, not an import/launch
attestation. Six disposable Git/file/proc contracts exercise source drift,
untracked modules, build mismatch, unsafe paths, process metadata and mid-probe
changes without using an appliance or actual backend process.

Even a full disk match reports `runtime_identity_verified: false`,
`served_frontend_verified: false`, `verified_running_revision: null` and
`live_authorized: false`. Actual served frontend bytes, trusted backend launch/
import identity, dependency/configuration and baseline/session recovery still
need independently collected live proof. Never fill those fields from Git HEAD,
disk hashes or an observer result alone. The narrow pilot integration below adds
independent controlled launch/build provenance and fresh actual observations.
Acceptance remains pending an explicit named start.

## Narrow pilot launcher

`qa_pilot.py inspect --baseline <private-record> --control-dir <fresh-private-dir>`
checks the reviewed controlled launch/build record against fresh host/guest/source/
configuration/dependency/Staff/served-byte observations, plus cached image/browser
pins. It sends fixed read-only code over bounded SSH and returns no secrets. The
standalone observer remains negative; the independent controlled deployment record
is necessary. Source/config/runtime inputs must precede the recorded process launch;
current file stamps, boot and master/worker identities must stay unchanged.

`qa_pilot.py run` permits one fixed batch (at most five cases, drawn only from
TC-SS-04, TC-ACC-09 and TC-NCPA-08). It requires the exact source-current queue, private baseline
checksum, initialized credential state, bounded private outputs and a separately
reviewed explicit start/expiry. No start record means no inspection, bridge or
container work. Canonical shared ledger consumption precedes the actual attempt.
Container removal, bridge shutdown, browser logout evidence and fresh baseline
checks are all required; any uncertainty halts without retry/reset/restore.
Each case gets an independent driver/bridge/container and private evidence. Results
and the batch journal are saved before the next case opens. Any non-PASS stops
remaining work; there is no automatic resume or diagnostic repeat in this lane.
The five-batch offline budget does not authorize extra batches in this launcher.

The first v4 browser/container attempt remains INCONCLUSIVE after the original
timing rejection. The separately authorized v2 recheck now passed the actual full
supervised result/cleanup path; see the [new report](../test-runs/2026-10-18-issue-211-ss04-recheck/REPORT.md).
Broader/unattended cases stay blocked. Neither scope allows a diagnostic repeat;
a later attempt/recovery needs separately reviewed scope/start.

The #211 offline timing fix has real pinned-worker and composed real-parser regressions.
It preserves the first pilot INCONCLUSIVE result, exact original halted-state
archive and original attempt/budgets. Separately authorized recovery and the fresh
v2 explicit start established narrow live acceptance without reclassifying v4.

## Explicit audited recovery exception

Paeng separately approved implementation of `qa_pilot.py recover`. It is not an
automatic retry, start or store reset. An expiring `supervised recovery` grant
binds the original ledger/attempt/evidence, new queue and unchanged target/baseline.
The caller holds canonical host/UUID locks, proves terminal metadata/logout without
accepting the old result, rechecks actual daemon/process/socket absence and baseline,
then archives exact original ledger bytes and appends a disposition. Attempts and
budget history remain unchanged; only its named new queue can consume a fresh slot.
Missing/changed archives and subsequent halts reject. The authorized actual
recovery retained the original ledger archive and added one audited disposition;
the separately started v2 attempt completed with accepted PASS/restored. A future
browser run still needs its own scope and explicit start; v2 is consumed.
See the [reviewed recovery scope](Issue_211_Recheck_Review.md).

## Reviewed next-assignment handoff

`qa_pilot.py handoff` is a separate audited operation after a complete recovered
queue. An expiring review binds the original ledger checksum, frozen prior queue,
owner/set, accepted evidence digest, new exact queue/owner/set and unchanged
target/baseline. The caller verifies every original PASS/restored item, terminal
container/bridge/session metadata, current daemon/process/socket absence and fresh
baseline before appending. The exact old ledger is archived; attempts, recovery
records and budgets are preserved and audited on later readiness checks. Missing
archives, incomplete outcomes, stale/foreign reviews, replay and an already-passed
ID in the new untested scope reject. This does not start a case or grant a new live
start. No actual handoff was applied during preparation. See
[the concrete two-case scope and start contract](Next_Permission_Batch_Review.md).

## Issue #214 seven-case execution readiness (2026-10-18)

See the [automation/manual handoff](Module_2-9_Automation_Handoff.md) for the
completed work, per-case automation prerequisites, and the cases deferred for
manual testing.

The current seven-case preparation snapshot is
[`2026-10-18-modules-2-9-adapters-v12.json`](queues/2026-10-18-modules-2-9-adapters-v12.json)
with two named sets: `modules-2-9-adapters-01` (five cases) and
`modules-2-9-adapters-02` (two cases). Both pass queue freshness/scope checks.
Their source-bound v6 cards contain reviewed action vectors, timeouts, cleanup,
private evidence paths and the inspected runtime baseline identity. Current case
fixtures remain `UNVERIFIED` on every card. See the
[fixture checklist](Module_2-9_Fixture_Plan.md) and
[case review](Module_2-9_Adapter_Review.md).

The read-only inspection proves only the controlled target/baseline. Before any
case action, each set still needs its exact fixture facts verified, a fresh
preflight, a named lab allocation and its own explicit start. The first set
cannot be treated as authorizing the second. Offline queue/docs checks are not
product test results.
