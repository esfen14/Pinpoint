# Agent Workflow and CI

**Last verified against the repository:** 2026-10-08

How work is picked up, verified and merged, by people and by coding agents.
Origin: the 2026-10-07 mentoring session (source of truth must be readable by
agents; loop engineering; last-mile checks in CI; reproducible environments).

## Where documents live

| Kind | Location |
|---|---|
| Specifications (current behavior and constraints) | `spec files/` |
| Plans, proposals, acceptance and remediation reports | `docs/plans/` |
| Operator and user manuals | `docs/manuals/` |
| Test plans and live-lab plans | `server/tests/plans/` |
| QA journeys, QA scope and the master QA test plan | `docs/qa/` |
| Tasks and open defects | GitHub issues |

See `docs/README.md` for the rules and lifecycle.

## One checkout per agent

Two agents (or an agent and a person) must never share a working tree: they move each
other's branches, mix uncommitted files into the wrong commit and can end up with a
stray commit on someone else's pull request. Give each agent its own git worktree:

```bash
scripts/agent-worktree.sh <name>     # creates ../<repo>-<name> on branch qa/<name>, with its own .venv and node_modules
```

Start the agent from that folder. It creates its own `issue-<n>-<slug>` branches from
`origin/main` (the workflow never runs `git checkout main`, which fails when `main` is
checked out in another folder). A branch can be checked out in only one worktree at a
time. Remove a worktree with `git worktree remove ../<repo>-<name>`; the issue
branches and their pull requests are unaffected.

## Source of truth

1. Tasks live in GitHub Issues, created from the **Task** template
   (`.github/ISSUE_TEMPLATE/task.yml`): title, problem and reproduction, finish
   condition, references. Chat messages are not a task record.
2. Behavior lives in `spec files/` (routed by `AGENTS.md`). A task that changes
   behavior names the spec section it changes.
3. Current gaps live in `Implementation_Status.md`.

## The agent loop

The executable version is `.agent/workflows/work-issue.md`, written for any agent.
Claude Code (`.claude/skills/work-issue/`) and OpenCode (`.opencode/commands/work-issue.md`)
load it through thin adapters, run as `/work-issue <issue number>`. The Codex adapter
([`.codex/skills/work-issue/SKILL.md`](../.codex/skills/work-issue/SKILL.md))
loads the same procedure for `$work-issue <issue number>`; any other agent is told
to follow the file. Codex adapters for
[`$qa-run`](../.codex/skills/qa-run/SKILL.md) and
[`$fix-found`](../.codex/skills/fix-found/SKILL.md) likewise load the matching
procedures in `.agent/workflows/`. It carries the loop, the 5-round limit and the stop conditions
below. Change the procedure only in that file; the adapters must stay a few lines long
so they cannot drift.

For every task, an agent repeats until the finish condition holds:

1. **Read** the issue and check that its finish condition covers every requirement
   it states (a gap is raised with a person, not skipped), then the **Required** documents for the area (`AGENTS.md`)
   and the source files they name.
2. **Write or update the test first** when behavior changes (TDD); the test
   encodes the finish condition.
3. **Implement** the smallest change.
4. **Verify** with the smallest relevant target, then `scripts/verify.sh <stage>`.
   Fix and repeat; do not widen scope to make a check pass.
5. **Update docs** in the same change: the owning spec, and
   `Implementation_Status.md` if a gap opened or closed.
6. **Verify the finish condition meets the issue**: re-read the issue and name,
   then run, the check that proves each requirement.
7. **Open a PR** from the template. CI is the last-mile check; a PR is done when
   CI is green, not when it works locally.

Stop and ask a person instead of looping when: a spec and the code disagree and
the user has not chosen, the change touches a sensitive module
(`Engineering_Standards.md`), or the same check has failed three times with
different fixes.

## Progress file and resuming

An agent that stops mid-job (session ended, limit hit, blocked on a question)
must not force the next session to start over. All job state is kept in
`.agent/progress/issue-<n>.md`, created from `.agent/progress/TEMPLATE.md`, on
the issue branch, and checkpointed after every round.

| Section | Holds |
|---|---|
| Header | Issue, branch, `Status:` (`in-progress`, `blocked`, `ready-for-review`) |
| Finish condition | The issue's items as checkboxes; ticked only when a check proves them |
| Plan | The whole plan, written before any code, as ordered checkboxes naming the files each step touches |
| Round log | One row per round: change, check run, result |
| State for the next session | Last command run, its result, hypothesis, and one specific **Next action** |
| Decisions and notes | Choices, things ruled out, questions for a person |

Rules:

- Write the plan first and push it (`scripts/agent_checkpoint.sh <n> "plan"`),
  so even a session that dies in the first minute leaves something to resume.
- After every round, update the file, then run
  `scripts/agent_checkpoint.sh <n> "<what changed>"`. The script validates the
  file, commits as `wip(#<n>): ...` and pushes. It refuses to run on `main`.
- To resume, run `/work-issue <n>` again (or tell your agent to follow the workflow file for issue `<n>`). It finds the branch, reads the file,
  re-runs the last check to see the real state, and continues at "Next action"
  without redoing ticked steps.
- The file is scaffolding, not documentation. Delete it (`git rm`) before the
  pull request is ready for review. CI fails a non-draft pull request that still
  contains one, and passes a draft. If the job is unfinished, open a draft PR
  and keep the file.
- `scripts/check_agent_progress.py` checks the structure (valid status, all
  sections, no template placeholders, a non-empty Next action). It runs in
  `scripts/verify.sh docs`.

## Test results

Where results go is defined in [`docs/test-runs/README.md`](../docs/test-runs/README.md):

| Result | Location |
|---|---|
| CI test output | JUnit XML in the `backend-test-results` and `frontend-test-results` artifacts of the Actions run, kept 30 days |
| Local test output | `test-results/` (git-ignored) |
| Live-lab and acceptance runs | A committed, sanitized `docs/test-runs/<date>-<slug>/REPORT.md` from `scripts/new_test_run.sh`, naming the commit tested, one row per case and an issue for every failure |
| Raw lab evidence | The harness `output_root` on the lab host; never committed |

## Test environments

| Layer | What it needs | How |
|---|---|---|
| Unit and mocked API tests | Nothing | `scripts/verify.sh`, and CI on every PR |
| Local lab (fast lane) | Docker | `scripts/lab up`, `scripts/lab smoke`; see [`docs/manuals/Local_Lab.md`](../docs/manuals/Local_Lab.md). A real Nagios and five target servers on an isolated network; not the installer, systemd, DHCP or NCPA installs |
| Isolated DHCP acceptance | Docker with `CAP_NET_ADMIN` in a dedicated switch namespace | Opt-in `scripts/dhcp-lab` controls and `scripts/dhcp-accept`; see the [Local Lab manual](../docs/manuals/Local_Lab.md#isolated-dhcp-lab) and [acceptance plan](../server/tests/plans/DHCP_LAB_ACCEPTANCE.md). Real `dnsmasq` and `dhclient`, limited to approved `10.79.0.0/28`; never run in CI or on a physical/VPN subnet |
| Real appliance and VM lab | Installer build, VirtualBox (this laptop) or libvirt (the retained lab) | `scripts/vmlab` with the `demo/` target VMs; plan in [`docs/plans/VM_Lab_Plan.md`](../docs/plans/VM_Lab_Plan.md). The snapshot holds Ubuntu + Nagios only, so it cannot go stale. The libvirt e2e harness in `server/tests/e2e/network_discovery/` is separate. Manual or scheduled, never on pull requests from forks |

Issue #274's [defense demo plan](../docs/plans/Defense_Demo_Lab_Plan.md)
now uses a laptop Docker pilot on a VirtualBox host-only network with an
owner-supplied Windows VM. `demo/demo presenter` controls the existing pinned
pilot containers; see the [pilot instructions](../demo/defense/README.md).
The following text records the earlier dedicated target-host preparation. Its proposed network/controller is not yet a
supported test environment or an approved additional scan scope. The existing
VM ownership and command-path review rules apply before implementation.
The versioned `demo/defense/manifest.json` lists the intended fifteen targets;
`demo/demo manifest` reports expectations with no live verification claim.
`demo/demo preflight` is read-only and checks host/Docker/configured VPN ranges,
private VM pins, the VM/process/NAT boundary, available memory/disk planning
and KVM availability. It refuses incomplete preparation. No lifecycle command
or new scan authorization is delivered by these initial read-only commands.
The [guest runtime preparation](../demo/defense/README.md) includes a generated
fourteen-target network-none Compose artifact, an image definition, fixed real
daemon controls and a root guest macvlan helper restricted to the two-target
architecture spike. Exact image/identity/mount/capability checks precede
attachment. A separate preview-first installer prepares a fresh Ubuntu target-host
and private media with a pinned SSH host key; it does not boot the VM. A one-use
guest boot service builds the image before any target starts. The first installation required console recovery; original pinned SSH and image
preparation are observed. Docker re-enables IPv4 forwarding after reboot, so the
guest helper refuses attachment. Durable forwarding, management-group cleanup,
reproducible setup, lifecycle, real protocol checks and the architecture spike
remain pending; this is not a supported live environment. The next offline
hardening adds no-auto-forwarding Docker settings, an every-start reset guard,
post-cloud-init account cleanup and a build-only gateway while the demo NIC is
down. Apply/retest these on the saved VM before starting any target. The private guest
helper can prepare only the two-target spike, dispatch fixed node JSON and stop
one checked container. Runtime/image fingerprints and MAC-matched manual parent
activation prevent stale builds or networkd link activation from bypassing the
guards. No live spike or additional scan scope is established by these APIs.
Offline defense input/ownership/resource/runtime contracts run in the docs gate.
Its separate [Windows preparation](../demo/WINDOWS_READY.md) now has an installed
Windows 10 Home test guest and locally verified NCPA agent, powered off at an
owned snapshot. Activation, appliance registration and complete defense-lab
acceptance remain pending; this adds no general QA scan authorization.

The [DHCP lab design](../docs/plans/DHCP_Lab_Extension_Proposal.md) records the
Docker feasibility decision and the separate lab's safety contract. The ordinary
fast lab and VM demo continue to use static addresses.

### VM control preflight

Mutating `scripts/vmlab` entries and the QA supervisor first acquire the fixed
private per-user host claim in `/tmp/pinpoint-qa-control-<uid>/controller.lock`
through `qa_control.py`. Nested controller calls must inherit the verified held
descriptor; environment/PID markers alone are insufficient. A driver calling
the controller under supervision must explicitly pass `Ledger.control_fd` and
`PINPOINT_QA_CONTROL_FD`. Different ledger roots still share host exclusion, but
persistent history requires one ledger. Do not delete/replace held lock files.
Direct VBoxManage/demo calls, other users/namespaces and legacy launchers remain
outside this cooperative guard; it is not an OS sandbox or live authorization.

Before VM-lab mutation, `scripts/vmlab preflight` must prove one same-user
VirtualBox controller, agreement between appliance UUID and the unique VM process under that controller,
and active runtime NAT forwarding sockets for both exclusive loopback listeners
(guest SSH/22 and web/80). A supplied session PID must also agree.
Powered-off state requires no remaining UUID process or endpoint listeners.
Mutation commands enforce this check at entry and recheck before SSH/key
bootstrap and start/power-off boundaries; inaccessible process identity, missing runtime forwarding evidence, duplicate
controllers and ambiguous/transitional states fail closed. It is a Linux-host
check; it cannot substitute for exclusive lab ownership. `preflight --json`
returns only timestamped host UUID/state/controller/endpoint observations, with
`live_authorized: false`; running app/frontend revision, baseline and recovery
remain separate missing proof. The collector rechecks session/process identity,
including kernel start ticks, and bounds each VBoxManage read to 20
seconds. The future driver must enforce a total deadline. See
[VM Lab Plan §4.0](../docs/plans/VM_Lab_Plan.md) for recovery and the disposable
endpoint-marker snapshot trial. Never treat a snapshot command's success alone
as proof that the endpoint is protected. The #162 owner accepted the lost edits as unrecoverable and authorized retirement
of the old lab disks. Positive ownership proof passed on the newly created appliance;
the original marker was restored through both actual SSH and HTTP endpoints,
and the rebuilt five-target lab passed its scoped smoke test. See the
[rebuild report](../docs/test-runs/2026-10-15-issue-162-snapshot-rebuild/REPORT.md).
`scripts/vmlab setup-admin` accepts the installer's previous email label and its
temporary-placeholder label, completes setup through the supported API and stores
credentials privately without printing their values. If installer credentials
cannot be parsed, it accepts saved host credentials only after signing in to the
configured endpoint and confirming through `/api/user/me` that both `needs_setup`
and `must_change_password` are explicitly false. Failed validation preserves host
state and installer credentials and exits with an error. Isolated command tests
cover these paths; the corrected helper has not been rerun on a live appliance.

### QA finding (qa-run) and agent loop safety constraints

The `.agent/workflows/qa-run.md` workflow governs agent-assisted execution of the
[module-based black-box catalog](../docs/qa/Pinpoint%20-%20Black-Box%20Test%20Cases%20by%20Module%20with%20Traceability%20Matrix.md).
It contains 231 TC cases and eight separate E2E scenarios. Historical catalog
results are human manual executions; new agent/human runs use separate attributable
reports. App/spec conflicts remain decisions, not automatic passes.

- **Scope preparation:** `scripts/qa_queue.py prepare` reads the module catalog
  and emits a version-2 JSON queue plus Markdown preview. Select `NAME:OWNER:MODULE,ID`
  sets; expand eligible cases once, report exclusions and snapshot procedures,
  expectations, prerequisite/global context, results, source hashes and exact target
  revision. Each case may carry an execution card; an absent/incomplete card blocks
  it. Group by module/person; optional ISO tags require a reviewed mapping. Reject
  legacy queue formats, duplicates, unknown/ineligible explicit IDs and overwrite.
  `show` displays scope and `check` rejects changed selected sources. Each set needs
  an explicit start; never automatically drain the queue. Local files are not
  distributed lab locks. Verify prerequisites per environment; separate machines
  run concurrently only with separate appliances AND targets. Preserve original
  human verdicts. New runs use attributable reports/index and separate journals.
  [Historical evidence review](../docs/qa/Historical_Evidence_Review.md) inventories
  candidates without conferring PASS. Reviewer decisions for the exact target,
  report/case hashes, item coverage and environment/source compatibility determine
  reuse. October 15 remains a provisional cutoff. See [queue guide](../docs/qa/QA_Run_Queues.md).
- **Source adapter coverage:** `scripts/qa_coverage.py` validates all current IDs,
  catalog/case/source hashes, review metadata and expected-item source assertions.
  The [coverage guide](../docs/qa/Automation_Readiness.md) distinguishes source
  implementation from live readiness and runtime outcomes. Queues snapshot coverage;
  cards bind its digest, adapter identity and exact argv. Unmapped/partial cards
  cannot open a case. The journal requires recorded action slots before PASS.
  Five Staff permission adapters have isolated offline collection/type checks;
  no live execution is implied. `scripts/qa_transport.py` and the runner's
  `--qa-preview` validate one unconsumed opened offline case and produce a JSON-only
  container contract: read-only source/root, isolated network, private separate
  evidence, and only two Staff credential mounts. Metadata checks never read
  credential values. Invalid/stale journals, private paths, used slots or draft
  cards reject the preview. The legacy runner rejects the current-case config
  before private-state/socket/Docker work. The narrow pilot below adds locking,
  fresh identity checks and composed dispatch; executing printed argv
  manually is not a supported workflow or authorization.
- **Supervisor lifecycle core:** `scripts/qa_supervisor.py` has no default driver or
  CLI of its own; the narrow pilot caller is described below. A separately bound explicit start/expiry, cooperative UUID
  lock, fresh matching runtime-driver receipts and durable fsynced running entry
  precede driver invocation. Restart/replay, missing supervised prior results and
  exhausted persisted budgets block. Cancellation/cleanup/proof/result failures
  persist a lab halt; validated restored FAIL remains FAIL. The existing item
  validator checks returned evidence. Synthetic-driver tests prove lifecycle
  sequencing only. The narrow pilot composes these controls; actual browser/container
  execution and post-case recovery validation remain pending. Never treat offline receipts or callbacks as live proof.
- **Runtime components:** `qa_process.py` runs only explicitly allowlisted trusted
  executables with reviewed argv, a restricted environment, bounded private output,
  time limits and POSIX-group TERM/KILL/direct-child reaping. Uncertain cleanup
  halts. It is not a sandbox or Docker-daemon/escaped-child cleanup mechanism.
  `qa_results.py` imports only one non-retried reviewed permission case, with fixed
  configuration, fresh timestamps and private expected-item/cleanup attachments.
  Only reviewed observation text is copied; incomplete/failed browser execution
  without failed-item evidence is INCONCLUSIVE. The transport bootstrap uses
  `umask 077`. Eight local-process and nine synthetic-report tests prove component
  contracts only. The narrow pilot below supplies integration; actual browser/container
  operation and post-case recovery still require the explicitly started pilot.
- **Concrete container lifecycle component:** `qa_container.py` requires a held
  host/UUID claim, durable matching consumed transport digest, scope-bound approved
  image ID, empty private evidence and existing private bridge socket. Independent
  bounded process/recovery runners retain private output with child `umask 077`.
  An fsynced unique intent precedes create; actual ID, image, owner, command, user,
  isolation and mounts are checked before bounded attach. Cleanup kills/removes
  only the identified owned container and proves absence through a successful
  daemon query. Failed/uncertain create, ownership drift, persistence/cleanup
  failures and existing intent halt without retry. Sixteen synthetic contracts
  are not live isolation/restoration evidence. No CLI/default production driver
  exists; production bridge wiring/runtime identity/baseline/session proof and explicit start remain
  required. Never manually invoke this component to bypass missing integration.
- **Owned bridge:** `qa_bridge.py` binds the consumed transport/host claim, retains
  its lock descriptor, checks same-user Unix peers and relays only to fixed
  `127.0.0.1:18080`. Time/connection/byte/buffer bounds, durable intent, custody
  checks and joined cleanup fail closed. The container component checks bridge
  custody before create/attach and after attach. Eleven Unix-only fixture tests
  are not live isolation proof. The driver still must stop the container, dispose
  the bridge and verify actual baseline/session recovery under its outer claim.
- **Deployment observations:** standalone `qa_deployment.py` reads expected source
  from full Git objects plus reviewed build hashes, compares stable canonical
  public artifacts and rechecks candidate process metadata without copying command
  arguments or environment values. Six Git/file/proc fixtures are not a live run.
  All positive runtime/served/version authorization fields stay false/null;
  trusted launch/import identity and actual served frontend bytes are separate
  missing proof. No SSH/restart/network/default live entry is added.
- **Narrow pilot integration:** `qa_pilot.py inspect` performs read-only checks;
  `run` supports only one TC-SS-04 initial attempt behind source-bound card,
  private reviewed controlled-deployment baseline and separate explicit start.
  It composes the shared ledger, bridge/container/process/results components.
  Fresh VM/boot/process/source/config/runtime/Staff/served-byte checks surround
  execution; local image and browser pins are checked without launching them.
  Missing proof, drift or uncertain session/resource cleanup halts. It never
  restores, resets users, enables schedules, scans or retries. Launch/build
  provenance is a reviewed trust boundary; disk or timestamp observations alone
  cannot create it. Broader/unattended cases remain blocked.
- **Partial-pass investigation:** Every catalog partial needs an evidence review,
  duplicate search, linked issue/disposition and next action in the
  [partial-pass register](../docs/qa/Partial_Pass_Investigations.md). The
  `investigate` queue purpose selects partials only and cannot open product cases.
  Reported gaps may be filed with human attribution; unknown observations require
  evidence clarification. Preserve original verdicts and apply normal live
  reproduction/repeat rules before `qa-found`.
- **QA batch throughput:** One owner's set may span multiple modules, expanded
  to fixed eligible IDs and ordered batches before review/start. The QA-specific
  five-round limit counts batches: up to five ordinary TC IDs per batch, five
  batches per session (at most 25 ordinary IDs). E2E, disruptive/fault,
  fresh-appliance and long cases each occupy one batch. Repeat at most once for
  diagnosis, retaining both attempts. No dynamic replacement of blocked IDs,
  reordered scope or reset by model/context changes. Save every case and checkpoint
  every batch. An explicit resume after the limit starts a new tracked session;
  another set needs its own start. Implementation and fix-found round limits are
  unchanged. Module ownership never grants shared-lab ownership or cross-module
  prerequisite execution.
- **Executor guardrails:** Every case needs a complete execution card: scope/owner,
  source/target revisions, verified prerequisites, exact tool/spec/command allowlist,
  writable outputs, bounded timeouts, evidence per expected item and written recovery.
  A missing field blocks execution. Executors cannot modify product/tests/selectors,
  expectations, scope or human results to pass. Uncertain steps stop the attempt;
  denied permissions, lost ownership, unsafe targets, secret exposure and failed
  cleanup stop the set. `scripts/qa_execute.py` validates offline session journals,
  complete adapter cards/hashes, exact ordered action slots, budgets and per-item
  evidence references. It never dispatches commands or verifies live preflight.
  Live recovery/resume, full case adapters and atomic scan guarding remain pending.
  Checksums detect changes, not hostile actors with file/shell access. Use reviewed
  supervision; do not claim an unattended runner or OS isolation from these tools.
- **Authority rules:** The behavioral specification wins; `Implementation_Status.md` records known gaps, not overrides. Conflicts without an explicit team decision require a `needs-decision` issue. Passing requires observed behavior.
- **Reporting rules:** A test failure is repeated exactly once before filing. Maintainers must search open and closed issues first; file use the Task template containing case ID and evidence; sanitize evidence (never paste passwords, credentials, tokens, SNMP communities, or raw database dumps). Defects determined to be installer bugs are written as notes for the owner, not filed against the application.
- **Safety boundaries:** Using `scripts/vmlab` and `scripts/lab` is permitted for QA sweeps; the libvirt e2e harness is strictly forbidden. Ordinary VM network scans MUST be tightly restricted to `10.77.0.0/28` using a guard. The separate opt-in issue #187 DHCP Docker acceptance may scan only `10.79.0.0/28` after its controller proves collision-free routing and exclusive ownership; this does not authorize other QA suites or a physical/VPN range. Overlapping discoveries are banned (#59). One appliance is tested at a time, checking disk/RAM capacity before provisioning.
- **Labels:** The loop uses `qa-found` for test plan failures and `needs-decision` for blocker/ambiguity issues.
- **Severity rubric:**
  - **High:** Blocks entire journeys, unrecoverable crashes, security breaches, data corruption.
  - **Medium:** Feature fails but has a workaround; significant UI defect affecting usability; correctable data error.
  - **Low:** Cosmetic issues, minor inconveniences, performance degradation within limits.
Record results of lab runs in `docs/test-runs/`.

### Find, fix, retest

`qa-run.md` records observed failures without fixing them. `fix-found.md` selects
eligible `qa-found` issues by severity then age and follows `work-issue.md` in a
separate issue worktree. It records skipped candidates, never weakens a QA case,
and opens at most three PRs in five rounds. Permission denial stops the loop.
Humans merge PRs; agents never merge. Only an actual merged fix plus a closed
finding makes affected new-suite cases eligible for `retest` in a reviewed queue,
with the original failure, PR and merge SHA retained. The reviewed finding/fix metadata is recorded in the evidence ledger and a new
queue; it never updates original human catalog verdicts. Two failed retests after separate merged fixes
label that finding `needs-decision` and stop work on the case. Synthetic workflow
demonstrations use scratch traceability data and do not establish product passes.
See `.agent/workflows/fix-found.md` for commands and written boundary checks.

### Current-case report timing

The narrow permission importer requires independent owned container attach launch
and completion UTC, monotonic elapsed time and the consumed remaining case budget.
Playwright 1.64.0 duration sums selected timeout slots; it is not a wall-clock end.
Evidence must fall between the current attempt start and actual attach completion,
within a positive window capped at 300 seconds and the remaining budget. Report
elapsed duration is bounded by 90 seconds and measured attach elapsed; attempt
duration is bounded by 60 seconds. Future timestamps receive no grace. Exact
source/case/initial-attempt/item checks and all cleanup requirements still apply.
No report-only inference authenticates a malicious same-user writer. See the
[timing investigation](../docs/qa/QA_Report_Timing.md) for pinned source semantics,
uncertainty and trust boundary. The real no-browser timing worker is included in
the frontend gate; it is synthetic harness evidence, never a case verdict.

### Explicit audited permission-pilot recovery

The narrow `qa_pilot.py recover` entry requires a separate expiring recovery grant,
current immutable new queue, original consumed scope and unchanged controlled
baseline. Under the canonical host/UUID claim it checks original terminal transport,
halted session and browser logout evidence without accepting the old case result;
then fresh read-only Docker ID/name absence, original same-user process/socket
absence and supported baseline proof. Failed observations or ambiguous state stop.

The ledger keeps an exact private checksum-named archive before appending a recovery
disposition and updating its active halt gate. Original attempts remain halted and
consumed, and session/batch budgets remain counted. Readiness validates the archive
and its history against unchanged attempt prefixes; only the recovery's exact new
queue may consume a slot, still under a separate live-start grant and fresh proofs.
No running-attempt recovery, ledger reset/relocation, implicit retry or resource
cleanup mutation is supported. A new halt needs new review. See the
[recovery contract](../docs/qa/Issue_211_Recheck_Review.md); same-user receipts and
cooperative locks remain a trust boundary, not cryptographic human authorization.

## Verification commands

| Stage | Command | Notes |
|---|---|---|
| Docs | `scripts/verify.sh docs` | VM ownership safety and administrator setup regression tests pass; agent progress files are well formed; relative links resolve; environment variables match the README table; browser routes match `App.tsx`, `pageAccess.ts` and the spec; module requirement mappings, derived status, queue/evidence/offline-executor regressions pass; fix-found queue and stop-rule contracts are present. Standard library only |
| Backend | `scripts/verify.sh backend` | Route and client-API drift checks, then `pytest tests/unit` in `server/` with `FLASK_DEBUG=1`; ~4 min, 2,167 passed / 14 skipped on 2026-10-08 |
| Frontend | `scripts/verify.sh frontend` | `npm run test`, `npm run build`, `npm run lint` (errors fail; warnings do not) |
| Everything | `scripts/verify.sh all` | Same stages as CI |

Live tests (`server/tests/integration/`, `server/tests/e2e/`) are never part of
CI or an agent loop without explicit approval; they need a lab Nagios.

## Continuous integration

`.github/workflows/ci.yml` runs on every pull request and on pushes to `main`.

| Job | Runs | Blocking |
|---|---|---|
| `docs` | `scripts/verify.sh docs` | yes |
| `backend` | Python 3.14, install `requirements*.txt`, `scripts/verify.sh backend` | yes |
| `frontend` | Node 22, `npm ci`, test, build, lint | yes |

Rules: CI uses no secrets and no network devices; every setting comes from the
environment (see the production settings table in `README.md`); a failing job
is fixed in the PR, never skipped. Protect `main` by requiring the three jobs.

Each test job uploads its JUnit XML as an artifact (`if: always()`, so failures keep
their results).

Not yet automated (see `Implementation_Status.md`): deployment, installer ISO
build and install test, spec-vs-code drift checks.

## Drift checks

A drift check fails when documentation and code disagree, so an agent can trust
the specs. Each is a script in `scripts/`; when one fails, fix the document (or
the code) in the same change.

| Script | Compares | Stage |
|---|---|---|
| `check_route_drift.py` | Every `/api` route registered in Flask against the `METHOD /api/...` entries in `Backend_Modules_and_Routes.md`. A first cell struck through with `~~` marks a documented-disabled route | backend |
| `check_client_api_drift.py` | Every `/api/...` string in `client/src` (including `${CONST}` prefixes) against the routes Flask serves, with the HTTP method when the call states it. A `${...}` placeholder matches any one segment | backend |
| `check_frontend_route_drift.py` | `<Route>` paths and page components in `App.tsx`, `PAGE_PERMISSIONS` in `pageAccess.ts` and the "Browser route catalog" table in `Frontend_Modules_and_Routes.md` | docs |
| `check_env_drift.py` | Environment variables the server reads (`os.environ`, `os.getenv`, `env_*` helpers) against the README "Production settings" table, which the installer builds `pinpoint.env` from | docs |
| `check_doc_links.py` | Relative markdown links in `AGENTS.md`, `README.md` and `spec files/` | docs |

Rules the checks rely on: put each route in its own table row (a combined row
such as "`/pause` and `/resume`" cannot be checked); a new environment variable
gets a README row in the commit that adds it.

Not yet checked: seeded permissions versus `require_permission` calls, the
permission list in `Backend_Modules_and_Routes.md` and the client permissions
(`Implementation_Status.md` already lists one known mismatch, the discovery stop
permission); component and module inventories; model inventories.

## Reproducible environment

`.devcontainer/devcontainer.json` gives Python 3.14 and Node 22 with
dependencies installed, so "works on my machine" differences are removed
before CI. Do not create bespoke VMs for development checks.

## Deployment environment (installer contract)

The installer repository (`lorraine-pangilinan/PinPoint-Installer`) builds an
Ubuntu Server 22.04.5 LTS appliance with Nagios Core 4.5.11, then clones `main`
into `/opt/pinpoint/Network-Diagnosis-System`, runs `npm ci && npm run build`
in `client/`, and runs `server/` under Gunicorn (1 worker, 4 threads, as the
`pinpoint` user) behind Nginx. Nagios's web UI moves to `127.0.0.1:8081`.

This repository's side of the contract, all implemented as of 2026-10-08:

- Settings come from `/etc/pinpoint/pinpoint.env` (table in `README.md`); a
  setting added to `server/config.py` is added to that table in the same change.
- `server/migrations/` is committed; every model change ships with a migration.
  The installer runs `flask db upgrade` (multi-database).
- `flask init-production` creates reference data and one administrator, flagged
  `Needs_Setup`: the installer's email (`admin-xxxxx@pinpoint.lan`) and password are
  placeholders, and the first sign-in must replace both through the setup window
  (`POST /api/user/complete-setup`). The VM lab's `setup-admin` completes it.
- `PINPOINT_SCHEDULER=1` only for the Gunicorn service.
- `flask restore-backup` (recovery runbook `docs/manuals/Backup_and_Restore.md`) checks `systemctl is-active --quiet pinpoint-gunicorn.service`, so the service unit name is part of the installer contract; the `pinpoint` account needs write access to its database files and `DATABASE_BACKUP_DIR`.
- The `pinpoint` account may write `hosts.cfg` and `plugin-services.cfg`, runs
  `nagios -v`, and may `sudo systemctl reload nagios`. The issue #129 installer
  extension additionally grants only the root-owned `pinpoint-apply-resources`
  helper with no arguments: validated owned-block data on stdin, fixed resource
  destination, retained external content and nagios:nagios 0660 metadata. It has
  been installed/tested on the QA appliance from the separate installer branch;
  production upgrades require that installer extension before macro generation.
  Writing to the plugin directory is intentionally not granted.

A change that breaks any item above breaks every installed server on upgrade;
raise it with the installer owners first. Installer code stays in its own
repository (`Implementation_Status.md`).

### Bounded permission batch handoff

The supported supervised permission lane is limited to TC-SS-04, TC-ACC-09 and
TC-NCPA-08 in one fixed serial batch. Each case needs its own source-bound card,
private evidence and fresh verification; results persist before the next case.
Any non-PASS stops remaining work. This does not enable generic unattended QA.
After the accepted pilot/recovery queue, `qa_pilot.py handoff` requires a separate
exact expiring review plus accepted prior items/terminal custody and independently
fresh absence/baseline proof. It archives exact ledger bytes and appends the new
queue hash, preserving original attempts, recovery archives and budgets. It grants
no case start. Missing archives, unfinished prior cases, old accepted IDs in an
untested scope or changed review reject. See
[the concrete permission batch review](../docs/qa/Next_Permission_Batch_Review.md).
