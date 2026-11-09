# Current-case adapter preparation

## 2026-10-19 Module 12 catalog review

Compared with `2e838077`, the branch records Module 12 PASS verdicts and changes
historical source references in Modules 22–23 and E2E. The Module 12 detailed
results now match the PASS summaries already recorded by this branch. All 239
cases retain their titles, priorities, requirements, steps, expected items,
dependencies and safety classifications. The coverage register's catalog/case
fingerprints were refreshed after this comparison; adapter source hashes,
coverage claims and expected-item mappings are unchanged. The generated status
view reflects the reconciled results. This review adds no live
execution, acceptance or authorization. Existing queues and cards still require
their normal freshness checks.

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

## 2026-10-19 existing-session login dependency review (#222)

Codex compared the written procedures, expected-item assertions and login/logout
fixtures for TC-ACC-09, TC-ROL-04, TC-SS-04, TC-HIS-01, TC-PLG-07,
TC-NCPA-08, TC-RPT-07 and TC-LOG-05 with the explicit sign-out contract.
Fresh browser contexts still receive 401 from the login route's session check,
then expose the same credential form. Staff's authorized landing remains Settings;
qa-view's remains Dashboard. The sidebar, direct-page and API-denial assertions
remain applicable, and cleanup still logs out and checks unauthenticated `/me`.
The affected login/API/App fingerprints were refreshed and the new `LoginRoute`
dependency was added to these mappings. Coverage statuses, expected-item mappings,
historical verdicts and execution permissions are unchanged. New queue scope and
fresh live prerequisites remain required; no live case was executed by this review.

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
[next batch review](../test-runs/2026-10-18-qa-next-permission-batch-review/REPORT.md).

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

## Data files and how each is produced

Every JSON file in `docs/qa/` is either curated by a reviewer and checked by a
script, or written by a script that refuses to overwrite its output. Neither kind
is edited to change a result.

| File | Kind | Script |
|---|---|---|
| `automation-coverage.json` | Reviewer-curated coverage registry | Validate with `python3 -I scripts/qa_coverage.py check`; its derived view [`Automation_Coverage.md`](Automation_Coverage.md) is regenerated with `python3 -I scripts/qa_coverage.py render --write` |
| `historical-evidence-review.json` | Reviewer-curated evidence decisions; read by `check_traceability.py` and `render_qa_case_tables.py` | Validated by `scripts/qa_evidence.py` (`validate_review`); [`QA_Case_Status.md`](QA_Case_Status.md) is regenerated with `python3 -I scripts/render_qa_case_tables.py --write` |
| `historical-report-inventory.json` | Candidate-report inventory with report hashes | `python3 -I scripts/qa_evidence.py --output <new file>` (refuses an existing output) |
| `queues/*.json` and their `.md` previews | Prepared QA queues (planning snapshots) | `python3 -I scripts/qa_queue.py prepare --set NAME:OWNER:MODULE,ID ... --output <new>.json --target-revision <sha>`; check with `qa_queue.py check --queue <file>` |

The one-off reviews that used to sit beside these files are dated reports under
[`docs/test-runs/`](../test-runs/README.md), for example the
[historical evidence review](../test-runs/2026-10-18-qa-historical-evidence-review/REPORT.md).

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
certify a new run. See [timing rule and investigation](../test-runs/2026-10-18-qa-report-timing/REPORT.md). JSON duplicate
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
See the [reviewed recovery scope](../test-runs/2026-10-18-qa-issue-211-recheck-review/REPORT.md).

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
[the concrete two-case scope and start contract](../test-runs/2026-10-18-qa-next-permission-batch-review/REPORT.md).

## Issue #214 seven-case execution readiness (2026-10-18)

See the [automation/manual handoff](#modules-2-9-automation-and-manual-test-handoff) for the
completed work, per-case automation prerequisites, and the cases deferred for
manual testing.

The current seven-case preparation snapshot is
[`2026-10-18-modules-2-9-adapters-v12.json`](queues/2026-10-18-modules-2-9-adapters-v12.json)
with two named sets: `modules-2-9-adapters-01` (five cases) and
`modules-2-9-adapters-02` (two cases). Both pass queue freshness/scope checks.
Their source-bound v6 cards contain reviewed action vectors, timeouts, cleanup,
private evidence paths and the inspected runtime baseline identity. Current case
fixtures remain `UNVERIFIED` on every card. See the
[fixture checklist](#modules-2-9-fixture-plan) and
[case review](#modules-2-9-current-case-adapter-review).

The read-only inspection proves only the controlled target/baseline. Before any
case action, each set still needs its exact fixture facts verified, a fresh
preflight, a named lab allocation and its own explicit start. The first set
cannot be treated as authorizing the second. Offline queue/docs checks are not
product test results.


## 2026-10-19 navigation terminology review (#233)

The sidebar and shell header now call `/system-status` Network Status. Codex
reviewed the eight Sidebar.tsx consumers (TC-ACC-09, TC-ROL-04, TC-SS-04,
TC-HIS-01, TC-PLG-07, TC-NCPA-08, TC-RPT-07 and TC-LOG-05). TC-SS-04 now
asserts the exact new hidden-link label and records that wording; its historical
case title, route, redirect and expected-item marker are preserved. Other adapters
still check their own hidden links or the same Overview/Settings-only list.
Reviewed source fingerprints are refreshed. Coverage status, catalog results and
live execution permissions are unchanged. This is source review and isolated UI
testing, with no live QA execution.


## Dashboard freshness dependency review (#238)

TC-DASH-07 still asserts Network Performance no-data values and absence of the
conditional resource heading. The new monitoring warning and freshness timer do
not change those assertions, prerequisites or cleanup. DashboardPage's hash and
its new hook/warning dependencies are recorded after source review. No coverage
status, catalog verdict or live execution permission changes. TC-DASH-06 retest
evidence remains a separate issue-specific report.


## Device drawer IP address history review (#277)

The device drawer gains an "IP address history" section (`DeviceAddressHistorySection`),
rendered after the Ports section as its own `h3` and table. Codex reviewed
TC-DI-02 and TC-DI-03: both scope their assertions to the Ports section
(`h4` group headings, `ul > li` rows, the reason paragraph), which the new
section does not touch, and neither asserts a heading list for the whole drawer.
Prerequisites, observations and cleanup remain valid. Only the reviewed
`StatusDetailDrawer.tsx` fingerprint is refreshed in `automation-coverage.json`.
Coverage status, expected-item mappings, catalog verdicts and execution
permissions are unchanged. This is source review, not a live QA result.


## Modules 2–9 preparation (issue #214)

The three records below were separate documents before issue #286: the
handoff, the case-by-case adapter review and the fixture plan. They are
preparation records for the Modules 2–9 queue, not execution results.

## Modules 2–9 automation and manual test handoff

Issue: [#214](https://github.com/esfen14/Pinpoint/issues/214)

This handoff separates source automation from actual execution. No Module 2–9
case in this queue has been run by the new adapter suite. The current executable
scope is [queue v11](queues/2026-10-18-modules-2-9-adapters-v12.json); its
seven adapters are ready at source level but blocked on case fixtures and a
separate start for each named set.

### Work completed

- Added source-reviewed Playwright adapters and explicit case selection for
  TC-ACC-08, TC-ROL-04, TC-DI-02, TC-DI-03, TC-DI-08, TC-HIS-04 and TC-DASH-07.
- Added a module-specific Playwright config, selection helper, QA TypeScript
  config, coverage mappings, exact expected-item markers and read-only guards
  for the device service dialogs.
- Extended the supervised pilot and result handling for these seven cases;
  generated source-bound execution cards, private evidence/output paths, and a
  seven-case queue split into two supported sets.
- Documented prerequisites, recovery boundaries, the fixture creation limits,
  and the 24 deferred candidates in the adapter review and fixture plan.
- Verified offline selection/collection, source coverage, result/transport/pilot
  contracts, QA TypeScript, frontend verification and docs verification. These
  are harness checks only.

### Cases with complete source adapters

These seven cases can be automated by the current supervised runner once their
exact fixture facts are verified. The cases are read-only; the adapters do not
create roles, accounts, devices, ports, or history.

| Case | Automated coverage | Still needed before execution |
|---|---|---|
| TC-ACC-08 | Super Admin alert checkbox/column and restricted-user checkbox visibility | Existing `qa-accounts` role and assigned user with the exact permission set; private credentials. |
| TC-ROL-04 | Dashboard-only sidebar, 13 protected page redirects, and three API 403s | Existing `qa-view` user with only `system.dashboard` and private credentials. |
| TC-DI-02 | Port group order, counts/nonempty groups, and TCP/UDP ordering | Exact existing device with Monitored, Suggested, Stopped and Archived ports. |
| TC-DI-03 | Held mismatched Suggested port and its single explanation | Exact existing port showing Held, Not used as intended, expected/found services and unacknowledged state. |
| TC-DI-08 | TCP known/generic service choices, UDP unsupported service, warning text | Exact editable TCP and UDP ports on the reviewed device; TCP options include `http`. Adapter blocks port writes and cancels dialogs. |
| TC-HIS-04 | Valid/invalid alert-history date-range API behavior | Super Admin history permission and a real alert event older than 25 hours within the rolling 30 days. Do not seed timestamps or change the clock. |
| TC-DASH-07 | Dashboard no-data cards | Appliance already has no ping check and no NCPA host/data. Do not remove monitoring to create this condition. |

Queue v11 places the first five in `modules-2-9-adapters-01` and the last two
in `modules-2-9-adapters-02`. They require separate explicit starts. The
controlled runtime baseline passed a read-only inspection on October 18, 2026;
that did not verify case fixtures. Every card currently records
`case_fixtures: UNVERIFIED`, so none is live-ready yet.

### Cases to handle manually or defer

The original candidate inventory contains 31 cases. After selecting the seven
above, 24 remain outside this automation run:

- **TC-ACC-10:** only E1/E2 have partial automation. E3 requires an unusual
  no-active-roles state; created account rows and audit entries persist. Use
  manual testing only on a disposable appliance with a reviewed recovery plan.
- **TC-DI-07:** an offline adapter exists, but the observed source behavior
  lowercases input while the case expects uppercase rejection. Manually inspect
  without saving and record the discrepancy; do not call it a pass until the
  expected behavior and result handling are resolved.
- **22 cases without complete adapters:**
  TC-NH-05, TC-NH-06, TC-NH-07, TC-DI-05, TC-DI-06, TC-DI-09, TC-DI-11,
  TC-DI-12, TC-DI-13, TC-DI-14, TC-DI-15, TC-DI-16, TC-DI-17, TC-DI-18,
  TC-DI-19, TC-ACK-04, TC-ACK-07, TC-ACK-08, TC-DI-10, TC-DASH-09,
  TC-SS-05 and TC-DASH-06. Follow the catalog procedures manually when the
  fixture is available. Cases that stop/resume services, change monitoring,
  acknowledge alerts, merge devices, fault services, or restart Nagios need
  their own isolation and recovery review first. TC-DI-19 is irreversible
  without a disposable target.

“Manual candidate” does not mean immediately runnable. Apply the catalog
prerequisites and the [fixture plan](#modules-2-9-fixture-plan) to each case;
missing prerequisites remain blocked. TC-ACC-09 and TC-SS-04 are not in the
24-case remainder: accepted supervised PASS reports already exist for them.

### Run status and next steps

No case in this seven-case queue has a result. The current status is:

1. Merge the adapter and handoff PR when reviewed.
2. Manually exercise the 24 deferred candidates whose prerequisites and
   recovery plan are satisfied; preserve exact observations and evidence.
3. For automated cases, use an appliance with the required existing fixtures or
   a separately reviewed isolated setup. Do not manufacture the no-ping/NCPA
   condition or aged history event in the shared lab.
4. Refresh the queue/cards and current preflight after fixture facts are known.
   Start each named set separately under `.agent/workflows/qa-run.md`.
5. Record any execution in a new attributable report under `docs/test-runs/`;
   do not edit the catalog’s historical result cells.

The [adapter review](#modules-2-9-current-case-adapter-review),
[fixture plan](#modules-2-9-fixture-plan), and
[automation readiness guide](#current-case-adapter-preparation) hold the detailed source,
coverage, scope and safety notes.

## Modules 2–9 current-case adapter review

Issue: [#214](https://github.com/esfen14/Pinpoint/issues/214)

This review maps the 31 catalog cases still listed as Not run after excluding
TC-ACC-09 and TC-SS-04, whose separate supervised reports record PASS. Source
coverage is a statement about reviewed test code; it does not indicate that an
appliance is ready, a case ran, or a live launcher accepts the case.

### Completed cases excluded from this queue

| Case | Current report result | Tested target | Expected items accepted | Report |
|---|---|---|---|---|
| TC-ACC-09 | PASS; restoration and baseline accepted | `299ab3ba7203c89a3ca5d8fabea42d9e5f239be2` | E1, E2 | [2026-10-18 next permissions](../test-runs/2026-10-18-next-permissions/REPORT.md) |
| TC-SS-04 | PASS; restoration and baseline accepted | `299ab3ba7203c89a3ca5d8fabea42d9e5f239be2` | E1 | [2026-10-18 SS-04 recheck](../test-runs/2026-10-18-issue-211-ss04-recheck/REPORT.md) |

The new Module 2–9 queue selects 31 other catalog cases and contains neither
ID. The catalog's historical `Result` cells and the generated source/result
view remain `Not run` by design: the workflow preserves original human entries
and records new executions in attributable reports. These linked reports are
the current execution record for these two cases; do not rerun them as untested.

### Case-by-case assessment

| Case | Expected items | Primary source and focused local tests | Prerequisite / mutation / recovery concern |
|---|---:|---|---|
| TC-ACC-10 | 3 | `ManageAccountsPage.tsx`; `ManageAccountsPage.test.tsx` | Partial adapter covers E1/E2. Needs an active role, a fresh run token, and a disposable appliance; creates two inactive accounts with alerts disabled. Rows/audit entries persist, so cleanup is not baseline restoration. E3 would require removing all active role options and remains blocked. A partial #191 browser report remains partial evidence. |
| TC-ACC-08 | 2 | `ManageAccountsPage.tsx`, `ManageRolesPage.tsx`; account/role page tests | Requires pre-created `qa-accounts` role and user. Read-only UI checks across Super Admin and restricted account sessions. |
| TC-ROL-04 | 3 | `ManageRolesPage.tsx`, `Sidebar.tsx`, `pageAccess.ts`; role/access tests | Requires a `qa-view` account. Iterates 13 pages and three APIs; needs separate restricted credentials and exact redirects/403s. |
| TC-DI-02 | 3 | `DevicePortsSection.tsx`, `devicePortsLogic.ts`; `DevicePortsSection.test.tsx` | Requires one device with ports in multiple lifecycle groups. Read-only; environment must provide each required state. |
| TC-DI-03 | 2 | `DevicePortsSection.tsx`, `devicePortsLogic.ts`; port component/logic tests | Requires a Suggested port that is both held and not-as-intended. Read-only; exact precedence/text needs a matching real record. |
| TC-DI-08 | 4 | `SetServiceDialog.tsx`, `devicePortsLogic.ts`, `DevicePortsSection.tsx`; service and port component tests | Requires reviewed existing TCP and UDP ports on one device. A network route guard aborts any attempted port PUT; both dialogs are canceled without saving. |
| TC-DI-07 | 3 | `SetServiceDialog.tsx`, `devicePortsLogic.ts`, `DevicePortsSection.tsx`; device port logic/component tests | Requires one editable port not already named `ssh` and a second editable port named `ssh`. Adapter blocks every port PUT and cancels both dialogs. The procedure says uppercase `SSH` is invalid; the component lowercases before validation, so E2 is a deliberate compatibility check that may expose an implementation/spec discrepancy, not an assumed PASS. |
| TC-DASH-07 | 2 | `DashboardPage.tsx`, dashboard metric components; `DashboardPage.test.tsx` | Requires no ping checks and no NCPA host. Read-only only after this baseline is independently observed. |
| TC-NH-05 | 2 | `NetworkHealthPage.tsx`, summary/trend components; `NetworkHealthPage.test.tsx` | Requires exactly one reporting ping host then a second host with new data. Adding a check and waiting changes lab config; no adapter may manufacture that evidence. |
| TC-NH-06 | 3 | `BandwidthCard.tsx`, `BandwidthChart.tsx`; `BandwidthCard.test.tsx` | Requires an SNMP device with monitored interface, traffic readings across four ranges, plus no-interface state. Read-only if fixture is already prepared. |
| TC-NH-07 | 3 | `FlapHistorySection.tsx`, `HostTable.tsx`, `DeviceInventoryPage.tsx`; inventory tests | Requires host flap history and flap-detection state. Read-only; four date windows and filtering need suitable real history. |
| TC-DI-05 | 4 | `DevicePortsSection.tsx`, `devicePortsLogic.ts`; `DevicePortsSection.test.tsx`, `devicePortsApi.test.ts` | Stops and resumes a monitored service. Reversible but changes Nagios config/state; verify service absence/return and restoration before continuing. Singleton batch. |
| TC-DI-06 | 2 | `DevicePortsSection.tsx`, device port API; `DevicePortsSection.test.tsx` | Holds a Suggested port, rescans, then disables/enables a plugin. Mutates discovery and monitoring configuration; needs a scoped target and verified restore. |
| TC-DI-09 | 3 | `DevicePortsSection.tsx`, `devicePortsLogic.ts`; device port tests | Pins and removes a service pin, then rescans. Changes service naming/config and needs preserved prior name plus rescan/recovery proof. Singleton batch. |
| TC-DI-11 | 3 | `DeviceMonitoringSection.tsx`, `monitoringState.ts`; `DeviceMonitoringState.test.tsx` | Requires normal, paused, address-unknown, missing, retired, merged, localhost, and precedence-combination rows. Read-only with prepared inventory. |
| TC-DI-12 | 3 | `DeviceInventoryPage.tsx`, `HostTable.tsx`, monitoring API; inventory tests | Checks default/filter values and an invalid GET. Read-only; host records must cover each monitoring label. |
| TC-DI-13 | 4 | `DeviceMonitoringSection.tsx`, `HostTable.tsx`, `DeviceInventoryPage.tsx`; monitoring tests | Pauses, rescans, resumes a device, and reads Dashboard/logs. Changes monitoring and Nagios configuration; singleton batch with restoration proof. |
| TC-DI-14 | 2 | `DeviceMonitoringSection.tsx`, monitoring API; inventory tests | Requires retired/merged, paused, and active devices. UI/API checks should be non-mutating and prove no state changed. |
| TC-DI-15 | 3 | `HostTable.tsx`, `DeviceInventoryPage.tsx`; inventory tests | Requires a paused device. Read-only; verify default Monitored view, Paused filter, last-known-status label, monitored-only summary. |
| TC-DI-16 | 2 | `DeviceIdentityReviews.tsx`, `DeviceInventoryPage.tsx`; `DeviceIdentityReview.test.tsx` | Needs empty and nonempty review states plus a hostname search. Read-only. Earlier #164 browser reports are partial; current UI/source compatibility still needs fresh execution. |
| TC-DI-17 | 3 | `IdentityReviewDrawer.tsx`, `DeviceIdentityReviews.tsx`; identity review tests | Requires unresolved review with two records and address history. Read-only; verify history is loaded only on button press and close does not write. Prior partial reports remain partial. |
| TC-DI-18 | 3 | `IdentityReviewDrawer.tsx`, permissions; identity review tests | Needs two distinct records and two roles with different edit permission. Read-only validation, but requires multiple authenticated identities. Prior report is partial. |
| TC-DI-19 | 3 | `IdentityReviewDrawer.tsx`, device identity API; identity review tests | Performs an irreversible merge with no undo. Must not be run without a separately reviewed disposable fixture and restoration plan; singleton treatment needs review. Prior report is partial. |
| TC-ACK-04 | 2 | `DashboardPage.tsx`, `RecentOutageTable.tsx`, acknowledgement modal; dashboard tests | Requires three active unacknowledged alerts, then writes acknowledgements. Must preserve an existing comment and prove all intended items; unacknowledge/recovery actions need a separately approved recovery plan. |
| TC-ACK-07 | 1 | `RecentOutageTable.tsx`, `DashboardPage.tsx`; dashboard tests | Requires same-severity acknowledged and unacknowledged alerts. Read-only once state exists. |
| TC-ACK-08 | 3 | Dashboard acknowledgement flow and History; dashboard/history tests | Acknowledges, repairs, then breaks a target again. Fault/recovery/re-fault is disruptive and must be isolated with explicit recovery; singleton batch. |
| TC-HIS-04 | 3 | `history.py`, History API client/page; `HistoryPage.test.tsx` | Read-only GETs verify valid/invalid ranges. E3 compares a real event older than 25 hours in the rolling 30-day range against a no-date response; if no such event exists, E3 is blocked rather than inferred from an empty response. |
| TC-DI-10 | 2 | `DevicePortsSection.tsx`, NCPA deployment/port API; inventory tests | Requires successful NCPA deployment. Read-only but a prior #129 report is partial and relevant source paths changed; preserve as partial and do not infer a pass. |
| TC-DASH-09 | 5 | `ForecastList.tsx`, `useForecasts.ts`, forecast types; forecast/dashboard tests | Requires three days of rising NCPA history, new host with insufficient history, and a flat host. Read-only display; data horizon cannot be fabricated or accelerated in a live run. |
| TC-SS-05 | 2 | `SystemStatusPage.tsx`, `ServiceStatusTable.tsx`, forecast types; service-status tests | Requires the same forecast fixtures as TC-DASH-09. Read-only display; verify a real rising metric and a low-history service. |
| TC-DASH-06 | 2 | `DashboardPage.tsx`, refresh settings and service overview; dashboard/settings tests | Changes refresh settings, stops and restarts Nagios. Privileged disruptive action; requires separately reviewed stop/recovery and restoration proof. Singleton batch. |

### Adapter and execution boundary

The existing current-case live path is the bounded supervised pilot. It supports
only the seven complete read-only adapters TC-ACC-08, TC-ROL-04, TC-DI-02, TC-DI-03,
TC-DI-08, TC-HIS-04 and TC-DASH-07 after reviewed cards, current fixture/baseline proof and explicit
start. TC-ACC-10 has only partial E1/E2 source coverage; it is excluded from the
live allowlist because E3 is unresolved and account rows persist. TC-DI-07 has a
complete offline adapter but is excluded due to the uppercase expectation mismatch
and current failure-result handling. The other 22 cases remain unmapped. Existing
component tests provide isolated UI evidence but
do not replace the written black-box procedures or live adapter assertions. An
adapter may be marked source-complete only where every expected item has an exact
assertion method, its prerequisites are explicit, and its mutations/cleanup are
reviewed. Partial historical reports (TC-ACC-10, TC-DI-10, TC-DI-16–19) do not
promote any item to PASS or authorize an unreviewed retest.

For this issue, no browser or product case has run; no Nagios fault,
configuration mutation, merge, acknowledgement, scan, deployment, or service
restart has occurred. A host-only read-only preflight was taken after the user
confirmed the same lab. Any queue produced here remains BLOCKED for live execution
until a supported launcher, reviewed cards, current lab proof, and separate start
exist. Existing successful permission runs are excluded and never replayed.

### Recorded completions and current host observation

- **TC-ACC-09:** complete supervised PASS for E1 and E2, with cleanup and baseline
  restoration, in [the October 18 permissions report](../test-runs/2026-10-18-next-permissions/REPORT.md).
- **TC-SS-04:** complete supervised PASS for E1, with cleanup and baseline
  restoration, in [the October 18 recheck report](../test-runs/2026-10-18-issue-211-ss04-recheck/REPORT.md).

These execution reports do not overwrite the catalog's original Result fields;
the QA workflow keeps new report outcomes separate from those historical entries.
The replacement untested queue must exclude both IDs and retain these report links.

On 2026-10-18 at 10:54 UTC, the read-only `scripts/vmlab preflight --json`
reported the same lab UUID (`351eb491-f5e1-4854-a7e4-68309ad774ad`) running with
host ownership and loopback endpoint checks passing. The supported read-only
`scripts/qa_pilot.py inspect` then passed against the reviewed controlled baseline
and confirmed that the served deployment still matches target
`299ab3ba7203c89a3ca5d8fabea42d9e5f239be2`. It launched no case/browser/transport
and reports no live authorization. A source comparison from that target to the
current repository base (`0f0d563e…`) found changes in DashboardPage,
DeviceInventoryPage and StatusDetailDrawer only for the unacknowledgement
confirmation prompt; that behavior is outside the Module 2–9 adapters.

The current baseline does not establish the required `qa-accounts`/`qa-view`
accounts, device/port fixture for TC-DI-02/03, or no-ping/no-NCPA fixture for
TC-DASH-07. TC-ACC-10 is source-partial only; its E3 branch, persistent account
disposition, and live recovery plan are unresolved. The current run-specific queue
`docs/qa/queues/2026-10-18-modules-2-9-adapters-v1.json` selects only the seven
complete read-only adapters and excludes the other 24 candidates from this run.
It still does not establish the required role/device/dashboard/history fixtures or
complete the live case cards; no case is ready to open. The broader 31-case v10
queue is retained as historical candidate inventory, not the active run scope.

#### Latest seven-case queue preparation (2026-10-18)

The active preparation artifact is now
[`2026-10-18-modules-2-9-adapters-v12.json`](queues/2026-10-18-modules-2-9-adapters-v12.json)
with its [Markdown preview](queues/2026-10-18-modules-2-9-adapters-v12.md).
It has two named sets because the supervised runner accepts one set of at most
five cases per invocation: set 01 contains ACC-08, ROL-04, DI-02, DI-03 and
DASH-07; set 02 contains DI-08 and HIS-04. Both set scopes pass
`qa_queue.py check`. The cards bind exact adapter actions, timeout envelope,
source review, current runtime baseline identity, private evidence/control/bridge
outputs and recovery steps.

The fresh read-only inspection at `2026-10-18T12:29:16.826139Z` verified the
controlled deployment target and baseline for the same lab, but case-specific
fixture inputs are absent or unverified. All seven cards therefore remain
BLOCKED. Account/role fixtures are not confirmed, exact device and port labels
are not confirmed, the no-ping/no-NCPA baseline is not confirmed, and the
qualifying real history event is not confirmed. The per-case evidence checklist
is in the [fixture plan](#modules-2-9-fixture-plan). No fixture setup, test
browser, case action, or result has occurred. The former queue/card drafts are
superseded by v11 for preparation; no start record has been created for either
named set.

## Modules 2–9 fixture plan

Issue: [#214](https://github.com/esfen14/Pinpoint/issues/214)

This is a preparation contract for the Module 2–9 queue. None of the states in
this plan has been verified on the appliance. The existing lab inspection proved
the served target and controlled baseline, not these case fixtures. Do not create
or alter a fixture until its exact operation, owner, evidence path, and recovery
are included in a reviewed card and the queue receives its separate start.

Fixture passwords belong in private same-owner files; never place values in this
file, a queue, a command line, a report, or a committed Playwright attachment.
Existing QA accounts or device records must be identified by exact reviewed
fixture identity before use. Similar-looking production or shared records are
not substitutes.

| Case | Required live fixture state | Preparation and recovery boundary |
|---|---|---|
| TC-ACC-10 | Super Admin; at least one active role; fewer than 99 existing accounts; two unique `example.invalid` addresses | The adapter creates two inactive accounts with alerts disabled. Rows and audit entries persist; this is not baseline restoration. E3 needs no active roles and remains blocked. |
| TC-ACC-08 | `qa-accounts` role with `account.view` and `account.edit` but no `account.alerts`; a user assigned to it | Create only through a reviewed account setup card. Preserve/deactivate the user and retain audit evidence; no direct database seeding. |
| TC-ROL-04 | `qa-view` role with only `system.dashboard`; a user assigned to it | Create through a reviewed role/account setup card. Verify the effective permission list before opening the case. |
| TC-DI-02 | One device with Monitored, Suggested, Stopped, and Archived ports | Read-only selection. Verify the device and each group before starting; do not change port state to satisfy the case. |
| TC-DI-03 | One Suggested port marked Held and Not used as intended, with expected/found names | Read-only selection. Verify exact port label and reason on the target before starting. |
| TC-DI-08 | One preexisting non-archived editable TCP port with `http` in service options and one preexisting non-archived editable UDP port on the reviewed device | Read-only dialog checks. Adapter blocks any port PUT and cancels both dialogs; verify exact labels, Set service actions, and service options before start. |
| TC-DI-07 | Two preexisting non-archived editable ports on the reviewed device: one whose service is not `ssh`, and one whose service is exactly `ssh` | Read-only validation checks. Adapter blocks any port PUT and cancels both dialogs; verify labels, current names, and Set service actions before start. |
| TC-DASH-07 | No ping check on any host and no NCPA host | Read-only baseline. Do not remove checks or deployments on the shared appliance to manufacture this state. |
| TC-NH-05 | Exactly one reporting ping host, then a second host with fresh reporting data | Requires a separately approved discovery/monitoring setup and wait for real data. Do not synthesize samples or claim a data horizon. |
| TC-NH-06 | SNMP device, monitored interface, traffic across all required ranges, and a no-interface device | Read-only selection. Require real observations in each range and a second device with no monitored interface. |
| TC-NH-07 | Host flap history and flap detection state spanning all requested date windows | Read-only selection. No synthetic flap rows or changed system clock. |
| TC-DI-05 | A monitored service that can be stopped and resumed | Mutating singleton case. Preserve current service/config state and prove restoration before any next case. |
| TC-DI-06 | Suggested unheld port, discoverable rescan target, and a plugin whose enabled state can be restored | Mutating case. Record exact plugin/port state before action and verify it after recovery. |
| TC-DI-09 | A monitored service eligible for pinning, with current name and rescan state recorded | Mutating singleton case. Preserve the original name and verify it after unpin/rescan recovery. |
| TC-DI-11 | Hosts covering normal, paused, unknown address, missing, retired, merged, localhost, and precedence combinations | Read-only selection. Each required label must have an independently identified real row. |
| TC-DI-12 | Inventory rows covering the required monitoring labels and filter results | Read-only selection. Include enough rows to verify defaults, filters, and invalid GET without changing inventory. |
| TC-DI-13 | A normal monitored device with a successful rescan path, dashboard row, and event log | Mutating singleton case. Record monitoring/configuration state; pause, rescan, resume, then prove all original state is restored. |
| TC-DI-14 | Retired/merged, paused, and active devices | Read-only API/UI validation. Verify the case does not change any row. |
| TC-DI-15 | A paused device with a last known status | Read-only selection. Verify the device is excluded by default and included by the Paused filter. |
| TC-DI-16 | Empty and nonempty identity-review states plus searchable hostname | Read-only selection. Prior #164 reports remain partial. |
| TC-DI-17 | One unresolved identity review with two records and address history | Read-only selection. Do not merge, dismiss, or otherwise resolve the review. |
| TC-DI-18 | Two distinct identity records and users with different edit permissions | Read-only validation. Use exact pre-created accounts; do not modify roles during this case. |
| TC-DI-19 | Two disposable records eligible for merge | Irreversible singleton case with no undo. Do not run without a separately reviewed disposable appliance and explicit recovery approval. |
| TC-ACK-04 | Three active unacknowledged alerts, including an existing comment that must be preserved | Mutating case. Acknowledge only listed targets; any unacknowledgement/recovery operation needs its own reviewed action. |
| TC-ACK-07 | Same-severity acknowledged and unacknowledged alerts | Read-only selection. Verify the exact pair and preserve both states. |
| TC-ACK-08 | Isolated service that can be acknowledged, repaired, and safely faulted again | Disruptive singleton case. Requires a fault/recovery/re-fault plan with exact target and verified restoration. |
| TC-HIS-04 | Super Admin with `system.history`; at least one real alert event older than 25 hours but within the rolling 30-day history | Read-only GETs only. Adapter compares the existing event with a no-date response; if no qualifying event exists, E3 stays blocked. Do not seed or edit history. |
| TC-DI-10 | Successfully deployed NCPA host with the protected NCPA port | Read-only check. Existing #129 report is partial; preserve it and verify current deployment state. |
| TC-DASH-09 | Three days of rising NCPA history, a new host with insufficient history, and a flat host | Read-only selection. The three-day horizon must be real and cannot be accelerated or fabricated. |
| TC-SS-05 | Same real forecast fixtures as TC-DASH-09, including rising and low-history services | Read-only selection. Verify metric source and history age before starting. |
| TC-DASH-06 | Saved refresh settings and a recoverable Nagios service/configuration baseline | Disruptive singleton case. Requires a separately reviewed service stop/restart and exact settings restoration plan. |

### Current fixture gate

#### 2026-10-18 execution-readiness check

At `2026-10-18T12:29:16.826139Z`, the supported read-only `qa_pilot.py inspect`
verified the controlled runtime baseline for lab
`351eb491-f5e1-4854-a7e4-68309ad774ad`, target
`299ab3ba7203c89a3ca5d8fabea42d9e5f239be2`, and baseline checksum
`da42da6cdbc38dab7ba6f9d96c2abd9cfb822123429fdd3f1e613ea50f8e07c3`.
This is environment evidence only; it is not a case run or authorization.
The private inspection is stored outside the repository. The approved private
fixture-input files for the two QA accounts and the device/port labels were
absent at inspection time. No credential values were read, and no accounts,
roles, ports, alerts, or other appliance records were created or changed.

Queue v12, `2026-10-18-modules-2-9-adapters-v12.json`, splits the seven exact
IDs into two runner-compatible named sets: set 01 has five cases in one batch;
set 02 has two cases in one batch. Each card now binds its source adapter,
per-case timeout, expected-item evidence path, private control/bridge paths,
container image, baseline hash and recovery instructions. Each card explicitly
records `case_fixtures: UNVERIFIED`, so the set remains blocked.

| Case | Fixture evidence still required before its set can start |
|---|---|
| TC-ACC-08 | Confirm the pre-created `qa-accounts` role grants account.view and account.edit but not account.alerts, assigned user exists, and both users' private credentials are available. |
| TC-ROL-04 | Confirm the pre-created `qa-view` account has only system.dashboard among protected page/API permissions and its private credentials are available. |
| TC-DI-02 | Identify the exact existing device and independently observe Monitored, Suggested, Stopped, and Archived ports and their expected ordering data. |
| TC-DI-03 | Identify an exact existing Suggested port that is held, marked Not used as intended, with the expected/found mismatch and unacknowledged state visible. |
| TC-DASH-07 | Observe that no host has a ping check and no NCPA host/data is present. Do not remove checks or deployments to manufacture this state. |
| TC-DI-08 | Identify exact existing editable, non-archived TCP and UDP port labels on the reviewed device; prove TCP options include `http`. |
| TC-HIS-04 | Confirm Super Admin has system.history and capture the identifier/time of a real alert event older than 25 hours but within the rolling 30-day range, without modifying history. |

After the fixture facts are collected, update the private input files and the
matching card's fixture status, then refresh/review the queue hashes and
preflight immediately before start. Cases that cannot meet a prerequisite stay
blocked; do not create or mutate shared appliance state as an improvised setup.
The two named sets require separate explicit starts under the shared workflow.

#### Creation feasibility for the requested fixtures

The current supervised pilot launches only the seven case adapters; it has no
fixture-provisioning action. Do not create records by direct SQL, API calls,
shell commands, or a host browser to get around that boundary.

| Fixture | Can it be created safely for this run? | Reason / required path |
|---|---|---|
| `qa-accounts` role and user (TC-ACC-08) | Only after setup support and a reviewed setup start | UI creation is possible in the product, but the role/user and login audit entries persist. The adapter only observes them and will not create, edit, or deactivate them. Use a disposable isolated QA appliance or explicitly accept these persistent records in a reviewed setup card. |
| `qa-view` role and user (TC-ROL-04) | Only after setup support and a reviewed setup start | Same persistence boundary; permissions must be independently verified before the case. Do not adjust an existing role or account. |
| Lifecycle port groups and held mismatch (TC-DI-02/03) | Must be observed on an existing fixture host or built in an isolated appliance | Port states come from discovery/monitoring data. Creating them would need network discovery and port lifecycle mutations, neither supported by this read-only run. Never repurpose a real/shared device. |
| TCP/UDP service options (TC-DI-08) | Usually observed, not seeded | Select existing editable, non-archived ports on a reviewed fixture host. The case adapter blocks port writes and cancels dialogs. If none match, prepare a disposable host with real listeners in a separate reviewed lab setup. |
| No ping and no NCPA (TC-DASH-07) | Cannot be manufactured safely in the current shared lab | This is a negative environment property. Removing monitoring checks or deployments would alter appliance state and is prohibited by this run. It must already be true on the selected appliance. |
| Qualifying alert history (TC-HIS-04) | Cannot be manufactured for this run | The requirement is a real alert event older than 25 hours within the rolling 30 days. Do not insert/edit history timestamps or change the clock; select a naturally qualifying event or wait for one. |

Therefore a single “create all fixtures” operation is not available. To make
the whole seven-case queue runnable, use an isolated QA appliance prepared with
the role/account and real port fixtures, and verify that its dashboard/history
already satisfy the two environment-dependent cases. Otherwise only the cases
whose existing fixtures can be proved are eligible; missing fixture cases stay
blocked. No snapshot is needed just to run the read-only cases, but fixture
provisioning on the shared lab must be treated as a separate state-changing
setup with its own recovery and approval.

The first batch contains four complete adapters and partial TC-ACC-10; the complete adapters depend on these unverified states:

- TC-ACC-08: `qa-accounts` role and user.
- TC-ROL-04: `qa-view` role and user.
- TC-DI-02: a host with the required port lifecycle groups.
- TC-DI-03: a held mismatched Suggested port.
- TC-DASH-07: no ping checks and no NCPA host.

TC-ACC-10 is only partially mapped and cannot be accepted as a complete case.
The supervised module dispatcher accepts only TC-ACC-08, TC-ROL-04, TC-DI-02,
TC-DI-03, TC-DI-08, TC-HIS-04, and TC-DASH-07, and only with complete source-bound cards, current
fixture/baseline proof, and an explicit start for the named queue set. It does
not create fixtures. Of the 24 cases outside its allowlist, TC-ACC-10 remains
partial, TC-DI-07 is source-complete but blocked on the uppercase expectation
mismatch and failure-result handling, and 22 remain unmapped. The seven accepted cases are currently blocked because their
fixture states have not been verified. Setup actions and recovery must be added
to reviewed cards before any fixture is created.

