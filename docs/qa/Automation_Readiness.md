# Current-case adapter preparation

[Automation coverage](Automation_Coverage.md) accounts for all 231 TC cases and
eight E2E scenarios. It is generated from `automation-coverage.json` and shows
source implementation, expected items still missing and unassigned executors.
It does not change the human catalog or certify any runtime PASS.

Five permission adapters are source-complete: TC-SS-04, TC-HIS-01, TC-RPT-07,
TC-LOG-05 and TC-PLG-07. Only TC-SS-04 is currently untested in the human catalog;
the other four remain excluded from default pending queues. An intentional
`recheck` needs its own reviewed assignment. The remaining 234 cases/scenarios
are explicitly unmapped, not automatically classified as suitable for automation.

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

No live card is complete yet. Actual account readiness, target revision, lab claim,
preflight, output lifetime, interruption/recovery and set start must be reviewed and
proved. Browser hooks may fail because a fixture is unavailable; that is not proof
of a product permission defect. E1 alone cannot pass a case if cleanup failed.
Other modules need their own assertion/fixture/recovery mappings; these permission
checks do not establish discovery, NCPA, report content, performance or E2E coverage.

## Verification

`scripts/verify.sh docs` checks the registry/derived view and isolated Python
contracts. `scripts/verify.sh frontend` type-checks the new config/adapter and runs
`node --test qa/selection.node.mjs` before existing frontend checks. Nine additional Python transport tests use synthetic private files and exercise
the preview/legacy rejection paths without external commands. Those Node
tests use Playwright `--list` with no browser or credentials: they prove exact
one-case/five-case collection, no setup dependencies/retries and rejected invalid
selection/private paths. They are harness checks, not live acceptance evidence.

## Supervisor lifecycle core

`scripts/qa_supervisor.py` provides an importable lifecycle core with **no live
command entry and no production driver**. Isolated tests supply a synthetic driver;
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

`qa_results.py` parses only the five reviewed permission adapters. It validates
pinned Playwright version/configuration, one project/case/initial attempt, no
retries/captures, fixed origin, consistent totals/status/timestamps and exact
expected-item/cleanup attachment identities. The actual process-launch time must
be supplied independently; a stale report cannot certify a new run. JSON duplicate
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
regressions. Nine synthetic-report tests validate parsing; they are not runtime
acceptance results.

These components are not yet wired to a production supervisor driver. Running
application/frontend revision proof, private bridge and
container lifecycle, real cleanup/recovery and explicitly reviewed live cards
remain pending. No live entry is enabled by their presence.

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
evidence. A private Unix socket must already exist; proving its fixed upstream
and creating/disposing the bridge remain the future driver's responsibility.
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

Thirteen synthetic command-response contracts exercise these paths. Local Unix
sockets are disposable metadata fixtures with no upstream. No Docker daemon,
container, browser, SSH endpoint, account or appliance is used by those tests.

A synthetic Playwright worker exposed an adapter preparation defect: Playwright
creates its artifact directory before its IPC worker reloads the configuration,
so unconditional empty-root validation rejected the real worker. Selection now
permits only the private owned `artifacts` directory for the pinned Playwright
worker entry with an actual IPC channel and expected worker indices. Environment
markers alone cannot relax the guard. Initial configuration and the container
lifecycle still reject reused evidence. The frontend gate has seven offline
selection/collection/worker checks; the worker fixture requests no page/browser,
imports no acceptance spec and produces no current-case result.

The same-day pilot scope is TC-SS-04 only, with no inherited human PASS reruns.
The user chose continued offline preparation. Real running frontend/backend
identity, bridge integration, initialized Staff baseline, complete live card and
an explicit named start are still needed; no claim that the pilot ran is made.
