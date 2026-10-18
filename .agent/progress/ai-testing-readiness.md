# AI automated testing readiness plan

Date: 2026-10-18 (Asia/Manila)
State: Implementation in progress — authorized offline tooling milestone (#206)
Tracking issue: [#206](https://github.com/esfen14/Pinpoint/issues/206); issue-scoped progress is [issue-206.md](issue-206.md).
Current authorization: implement readiness tooling. [Issue #206](https://github.com/esfen14/Pinpoint/issues/206)
tracks the offline milestone in an isolated checkout. No live case execution, lab
connection, provisioning/reset or fault injection is authorized by that milestone.
The original planning-only instruction was superseded by the user's go signal.

## Finish condition

This checklist defines readiness to execute the new black-box cases. It does not
claim that the product passes or that every case can run without human involvement.

- [x] The new catalog, historical human results and new execution records have clear, validated ownership.
- [x] Queue preparation/checking and the documentation gate work against the new catalog without restoring retired inputs.
- [ ] Every selected case has an unambiguous expectation, executor, environment, prerequisites, evidence and restoration procedure.
- [ ] Every selected case maps to a specific tool/spec/project, fixture, assertion and evidence output using the reviewed testing stack.
- [ ] Historical runs have been mapped to current expectations with linked evidence, an agreed cutoff and a version/impact check; only uncovered or invalidated coverage enters the new-execution queue.
- [ ] The selected lab and automation tools enforce the approved boundaries and fail closed when those boundaries cannot be proved.
- [ ] A reviewed pilot queue is ready, with its outstanding human decisions clearly shown.
- [ ] After a separate explicit start, the pilot demonstrates execution, reporting, failure handling and verified restoration.
- [ ] Unattended testing is enabled only for cases with deterministic execution and recovery; remaining cases stay explicitly human-assisted or blocked.

## Implemented offline milestone

- Shared parser validates all 231 TC/eight E2E procedures, phases and requirements;
  conflicting human results remain flagged.
- Queue v2 supports module/person assignments, fixed batches, exact IDs, exclusions,
  source snapshots/freshness, optional cards and reviewer-bound historical reuse.
- Forty-one post-cutoff-directory-date reports are inventoried; six current-case
  mappings are partial. No inherited full-case PASS or cutoff decision is invented.
- Offline session validation rejects missing owner/start/preflight attestations,
  incomplete/changed adapters, wrong action slots, exhausted budgets, incomplete
  PASS evidence and failed cleanup. It dispatches no live commands and is not an
  OS sandbox. Live adapter completion, preflight, enforced scan guard, recovery/resume
  and pilot runs remain separate pending work.
- Current/historical links and docs checks have migrated. `scripts/verify.sh docs`
  is green (66 isolated checks). Full local verification passed 4310 backend and
  1003 frontend tests, build and lint (zero errors). [Draft PR #207](https://github.com/esfen14/Pinpoint/pull/207)
  contains the offline milestone; final-head CI is checked separately.

The original checklist below is intentionally retained. Only mark its broader
items complete when the whole requirement (including live evidence where needed)
is proved; offline tooling alone does not satisfy full unattended readiness.

## Current baseline (planning snapshot, retained for context)

- Case source: [Black-Box Test Cases by Module with Traceability Matrix](../../docs/qa/Pinpoint%20-%20Black-Box%20Test%20Cases%20by%20Module%20with%20Traceability%20Matrix.md).
- Catalog: 231 TC cases across 23 modules, plus eight distinct E2E scenarios.
- Existing recorded results were executed manually by a human. They are not AI-run evidence.
- Earlier review found 26 summary/detail result conflicts. Recount against the approved catalog revision before reconciling them.
- [QA Run Queues](../../docs/qa/QA_Run_Queues.md) and [qa-run workflow](../workflows/qa-run.md) already describe the new IDs, preserved human results and temporary reviewed Markdown queues.
- `scripts/qa_queue.py` still imports the old table renderer, reads the removed plan/matrix and validates legacy IDs/ISO groups.
- The old plan, traceability matrix and paper tables are deleted in the current working tree; the new catalog is untracked. Preserve these owner changes pending the agreed migration.
- The last `scripts/verify.sh docs` stopped at broken references to the removed QA documents. Later legacy validators/rendering tests also need migration.
- Earlier focused verification passed nine fix-found workflow contracts, one queue workflow contract, changed-document link checks and `git diff --check`. These are documentation checks, not product QA.
- [Deterministic browser-to-Nagios testing proposal](../../server/tests/plans/TEST_APPROACH_ADJUSTMENT_PLAN.md) remains proposed/deferred. It is not an implemented runner or authorization to use its legacy libvirt harness.

## Proposed testing stack and how the AI uses it

Proposed default: **TypeScript Playwright tests in Chromium, launched by the AI
through the existing isolated lab runner**. Python handles catalog/queue/evidence
processing and, where needed, orchestration. Reuse the repository's existing stack;
do not introduce Selenium, a second Python browser framework or a new load-testing
service without a concrete unmet requirement.

The AI reads the reviewed queue, implements/reuses the mapped tests after approval,
launches the approved subset through shell commands, and interprets the resulting
assertions/reports. It does not decide that a case passed from prose, visually guess
unmeasured values or repair the product during an unattended run. An exploratory
AI-assisted browser session must be labelled separately from scripted automation.

| Testing need | Tool the AI will use | Execution / evidence | Current state / needed work |
|---|---|---|---|
| Browser actions and visible assertions | `@playwright/test` with TypeScript and the matching Chromium build | Click/type/navigate using accessible locators; assert controls, messages, tables and state transitions | Already pinned to Playwright 1.64.0 in `client/package.json`; specs live in `client/e2e/`. Map existing specs and add missing current-case assertions. |
| Isolated browser launch | `scripts/playwright-lab` and `client/playwright.config.ts` | Run selected projects/specs in Docker with `--network none`; the private Unix-socket bridge exposes only the approved appliance origin | Exists. Keep this boundary for live credentials; validate runtime prerequisites and adapt selection/output for new-case queues. |
| Login, roles and independent sessions | Existing Playwright setup projects and separate browser contexts | Disposable Super Admin/Staff/limited-role sessions; assert real login/forced-change/denial behavior | Helpers exist; additional role fixtures and fresh-first-run profiles need explicit setup. Credentials remain private. |
| Direct API negative/permission cases | Playwright `APIRequestContext`, including the browser context's request client where authenticated state is required | Assert response status/body and persistence/non-mutation; run through the same isolated origin | Reuse the installed test framework. Add mapped API tests only where the case calls for API requests; never replace a required UI action. |
| Appliance/target lifecycle | `scripts/vmlab` with VirtualBox and its ownership preflight; `scripts/lab` for compatible Docker cases | Establish/reset approved baseline, target health and verified endpoint restoration | Existing controllers; environment choice and mutation commands must be declared per queue. No libvirt harness. |
| Controlled fault injection and recovery | Narrow shell/SSH fixture operations via the approved lab controllers | Stop/start only the named disposable service/listener; journal each change and verify restoration | Some helpers exist; add missing reversible fixtures/recovery safeguards. Never use shell to bypass the product workflow under test. |
| Real monitoring and alert correlation | Browser plus read-only API/Nagios CGI/status/log observations through approved lab access | Correlate a fresh Nagios state/event with Pinpoint's UI/history and required notification evidence | Existing live tools/reports can be reused after mapping. Bound polling and freshness checks; unit mocks do not prove this path. |
| Timing, performance and four-hour stability | Playwright/Node monotonic timing (`performance.now()`), or Python `time.monotonic()` for controller measurements, plus bounded repeated observations | Record defined start/end events, timestamps, load and measured durations; validate cross-system clock alignment where needed | Implement case-specific measurements. Do not use AI response/tool-call duration as application latency or add an unrelated load tool by default. |
| CSV/Excel exports and print views | Playwright download events, browser print-view assertions and Node filesystem/content checks | Verify downloaded filename/format, expected rows/columns/values and print-view content according to the case | Reuse existing export specs. Add format-aware checks; a download or successful HTTP response alone is insufficient. Review any additional parser dependency first. |
| Email delivery | Real configured SMTP path plus actual mailbox confirmation when the case requires it | Correlate event/dispatch with recipient inbox evidence, or an approved isolated mailbox fixture for cases allowing one | SMTP/API/browser checks exist. External mailbox access is not assumed: retain a human step until an explicitly configured mailbox reader is available. SMTP acceptance is not inbox receipt. |
| Case selection and historical evidence reuse | Python standard-library catalog parser, migrated `scripts/qa_queue.py` and reviewed case-to-report map | Produce/check fixed case sets and exclude accepted unchanged historical coverage | Queue script exists in legacy form; new parser/schema and reuse-aware selection are planned work. |
| Result collection and reporting | Playwright JSON output; Python report/evidence processing; `scripts/new_test_run.sh` | Unique per-run raw artifact directory outside restored guests; sanitized `docs/test-runs/.../REPORT.md`, index and queue log | JSON reporter and report helper exist. Add run IDs, current-case mappings, partial/inconclusive states and historical-credit fields. |
| Unattended orchestration | A small Python controller around existing queue, lab and Playwright tools | Validate manifest, hold one lab lock, execute dependencies sequentially, journal interruption, recover and finalize a complete report | Not implemented for this suite. Proposed `scripts/qa_execute.py` is a planned filename, not an available command; confirm placement during implementation. |
| Implementation regression checks | `scripts/verify.sh docs/backend/frontend/all` using existing standard-library checks, pytest, Vitest, TypeScript build and lint | Verify changes to tooling or product code as applicable | Exists; docs migration must first remove retired-source assumptions. Passing these checks is not evidence that the black-box cases ran. |

Implementation files already inspected for this choice:
[Playwright config](../../client/playwright.config.ts),
[package manifest](../../client/package.json),
[isolated launch helper](../../scripts/playwright-lab), and
[Playwright setup guide](../../docs/qa/Playwright_Setup.md).
The older deterministic proposal suggests Python Playwright; this plan instead
proposes the existing TypeScript suite to avoid parallel browser stacks. Align
that proposal if this choice is approved; it is not automatically superseded.

### Tool-readiness tasks before the pilot

- [ ] Confirm this stack during plan review and freeze the runtime/browser/container versions used; package declarations alone do not prove the runtime is installed or the lab is ready.
- [ ] Verify Docker, VirtualBox where needed, Node/Python, `socat`, Chromium system libraries, private credential files and the Unix-socket bridge during an authorized environment preflight.
- [ ] Add a case-to-tool/spec/project mapping for every selected ID, including required fixtures, assertion method, evidence output and cleanup. Record reuse rather than claiming every existing spec covers the new case in full.
- [ ] Make queue selection resolve to an exact spec/test allowlist; reject unmapped IDs, and never launch the default entire Playwright project list as a substitute for the selected queue.
- [ ] Use one worker and no silent automatic retries for acceptance (`--retries=0` or equivalent reviewed configuration). Existing config permits two CI retries; prevent that from hiding a first failure. Any diagnostic repeat is a separately recorded attempt under the QA policy.
- [ ] Persist unique run-specific JSON/download/journal outputs before reset or another launch; the current single `playwright-results.json` path must not overwrite earlier run evidence.
- [ ] Keep login trace/video/screenshot capture disabled. Capture only authorized non-secret evidence after login, sanitize reports and never publish raw auth state or credential-bearing artifacts.
- [ ] Prove fixture/recovery and runner failure handling with isolated self-tests before approved live pilot use. Mark human-dependent or unmapped cases blocked instead of switching to an unreviewed tool.

## Plan

Complete phases in order. Items may be implemented together when they share the
same contract. Implementation approval does not automatically start a live queue;
the saved queue/set still needs its explicit start under the QA workflow.

### 1. Establish the approved source and execution model

- [ ] After the go signal, establish a real tracking issue and dedicated implementation checkout/branch; use an issue-scoped progress file without mixing owner changes into the work.
- [ ] Freeze the catalog revision/content hash, review the existing deletions and identify which source changes belong in the migration.
- [ ] Review the proposed TypeScript Playwright/Chromium stack above and the first milestone: a scripted pilot launched by the AI, with exploratory AI-assisted cases labelled separately. Build shared catalog/queue/reporting support first; unattended orchestration remains a later gate.
- [ ] Inventory all live references to the retired documents, old case IDs and ISO queue assumptions across `.agent/`, skill/command adapters, `scripts/`, `docs/`, `spec files/`, `AGENTS.md`, client E2E specs and CI.
- [ ] Keep historical journey reports and their original IDs/results intact. Use an archived source revision for historical links where needed; do not remap historical evidence to new case IDs without review.
- [ ] Establish ownership: catalog = procedures/requirements plus preserved human history; run reports = new observed executions; queues = reviewed assignments/eligibility. Decide whether a derived current-status view is useful; never create competing editable ledgers.

Expected output: agreed source/result contract and migration scope.
Files: current catalog, QA workflow/guide, tracking progress, owning workflow/status specifications.

### 2. Reconcile eligibility and make selected cases executable

- [ ] Recount and list summary/detail conflicts by ID, copying both human entries and observations into a decision record.
- [ ] Obtain the human tester's clarification where possible. Preserve original observations and record who resolved each conflict and why; never infer missing tester/date/SHA/evidence.
- [ ] Keep unresolved cases `needs-decision` and exclude them from ordinary pending queues. An explicitly approved diagnostic recheck may gather new evidence without changing the old result.
- [ ] Handle EDG/SEQ tables that have no Result column using detailed Result lines; distinguish absent columns, missing verdicts, free-text notes and explicit Not run.
- [ ] Review the four recorded failures, two partial passes and unclassified acknowledgement-filter observation; search existing issues by ID and symptom before deciding finding/retest/recheck eligibility.
- [ ] Check selected expectations against behavioral specifications and team decisions. Document app/spec conflicts rather than weakening the case to match current behavior.
- [ ] Specify exact timing boundaries, clocks, target counts/load, polling limits, warm/cold assumptions and sampling rules for NFR cases. Preserve specified thresholds; ask for decisions on undefined rules.
- [ ] Define state-based prerequisites and concrete setup data for selected cases: accounts/permissions, hosts/services, active incidents, identity candidates, SNMP devices, deployed NCPA agents and sufficient history.
- [ ] Classify each selected case as AI-assisted, scripted, human manual or mixed. Identify external inbox checks, subjective usability observations, installer steps and inaccessible targets that need a person or additional fixtures.
- [ ] Record an explicit automation coverage matrix. A ready pilot needs its selected cases resolved; unresolved cases elsewhere can remain excluded with reasons. Full-suite automation requires every case classified, not falsely labelled automated.

Expected output: reviewed eligibility/ambiguity list and execution metadata for selected cases.
Files: catalog decision notes, queue/report metadata and relevant requirement clarifications.

### 2A. Reuse applicable historical runs before selecting new executions

User direction: use applicable old test runs to reduce duplicate testing, with the
source run attached. This is evidence reconciliation, not permission to execute
cases or rewrite human history. Perform it before final queue selection.

Proposed cutoff: **2026-10-15 00:00 Asia/Manila**. This excludes the October 13–14
transition by default until the actual migration/release boundary is identified.
A report date is only an initial filter: a report written after the cutoff may
still have tested an older build. Check execution time and actual product revision.
If the significant change landed later, move the baseline to that revision.

- [ ] Confirm the cutoff/transition commit as part of plan review. Use October 15 as the provisional default; do not claim it is already approved or proves compatibility.
- [ ] Inventory `docs/test-runs/` using the index and report bodies. Select post-cutoff execution candidates, retaining tested application/installer SHA, timestamp, executor, environment, exact case observations and limitations.
- [ ] Keep pre-cutoff evidence as background or defect history by default. An exception needs explicit rationale/review and the same full coverage/version checks; do not automatically import old passes.
- [ ] Map old report case IDs to current `TC-*` or `E2E-*` expected items by observed behavior, not title similarity. Attach a clickable report link with section/row identification and explain the mapping.
- [ ] For each mapping, compare report scope, steps, prerequisites, permissions, environment and every current expected item. Record exact items covered and missing, including negative/boundary checks. A report's overall Pass is not a blanket case pass.
- [ ] Compare the actual tested source/configuration and relevant dependencies against the target build, including shared auth, polling, Nagios generation, schema, installer and integration changes. Verify branch changes were integrated or equivalent. Missing SHA, unexplained dirty runtime changes or unavailable provenance means current-build reuse remains unverified.
- [ ] Classify each mapping as `accepted historical coverage`, `partial historical coverage`, `retest required`, or `not applicable`, with reason, reviewer and target revision. Keep these evidence classifications distinct from execution verdicts.
- [ ] Exclude fully accepted unchanged coverage from redundant execution by default. A linked historical PASS can satisfy coverage for the reviewed target without claiming it was executed again, executed today or executed by an AI.
- [ ] Queue only missing checks for partially covered cases when a documented subset preserves their prerequisites. Keep the whole case partial until every expected item is supported; otherwise rerun the full case.
- [ ] Combine reports only when their versions/configurations and observed checks are compatible. Do not combine independent module passes into an E2E pass: an E2E scenario needs its integrated sequence and expected state transitions observed.
- [ ] Require fresh execution when relevant behavior/dependencies changed, a fix is being verified, expectations expanded, prior evidence conflicts or is incomplete, or environment differences invalidate the claim. Keep actual stale evidence rather than deleting it.
- [ ] Prefer fresh measurements for performance, polling/timing, soak and environment-sensitive delivery cases on the target baseline. Prior timing/email evidence can be supporting history; specify why it remains valid if reuse is proposed.
- [ ] Preserve original report verdicts and executor attribution. The catalog's existing human results remain human results; historical reports naming Playwright/Codex or mixed execution retain those labels and never become human results by import.
- [ ] Reconcile historical coverage with the catalog's conflicting human entries explicitly. A newer report supports a new evidence decision; it does not silently erase a prior human failure or unexplained observation.
- [ ] Add linked historical coverage references beside current case IDs in a separate reviewed evidence view, or in clearly labelled catalog evidence notes, using one authoritative mapping. Do not edit old Result fields to imply a new run. Choose the exact storage/schema during implementation.
- [ ] Track totals for accepted historical coverage, newly executed cases, partial coverage, required retests and pending cases separately. Count each unique case once; retain multiple supporting reports/attempts without inflating completed totals.
- [ ] Include this reuse policy in the QA workflow/queue guide and automated eligibility checks. Test rejection of a late-dated report against an obsolete build, partial-to-full promotion, incompatible report aggregation and stale accepted evidence after a relevant change.

Historical reports inspected during planning provide candidate evidence, not an
accepted mapping:

| Candidate | Potential overlap | Limitation requiring review |
|---|---|---|
| [October 17 remote-restart browser run](../../docs/test-runs/2026-10-17-issue-182-playwright/REPORT.md) | NCPA cleanup/settings and remediation permission/action controls | Covers RR-12; only part of broader flows. One load-error check was intercepted; does not prove another Nagios failure chain. Compare product `910d6f99` with the target build. |
| [October 17 reports browser run](../../docs/test-runs/2026-10-17-issue-134-reports-documentation/REPORT.md) | Populated report views and CSV exports | Does not establish every report case, export format or negative condition. Used an older appliance with relevant-file equivalence at that time; later service-report changes require a new impact check. |

Expected output: reviewed case-to-report evidence map and a smaller queue containing
only genuinely missing, invalidated or explicitly requested regression coverage.
No current case receives inherited credit merely because its report was attached.

### 2B. Prepare multi-person module assignments and bounded execution cards

User direction: support larger QA assignments by module/person and explicit
constraints suitable for a less capable executing model. The QA guide/workflow
now document this contract; the independent enforcement below remains todo.

- [ ] Prepare owner-to-module assignments and expand each to fixed eligible IDs after evidence review. Show exclusions, conflicts and accepted historical coverage; do not allocate the same case to multiple owners.
- [ ] Verify each person's own appliance AND targets or agree on exclusive access windows. Module ownership does not reserve the lab or establish another module's prerequisites.
- [ ] Partition each set into fixed ordered batches of at most five ordinary TC IDs. Isolate every E2E, disruptive/fault, fresh-appliance or long case in a single-case batch, following catalog phases.
- [ ] Enforce five batches per session (up to 25 ordinary TC IDs) with persistent session/batch counters. Explicit resume creates a new session; compaction, tool/model changes and handoff must not reset a session's counters.
- [ ] Make execution cards complete before start: source/target versions, exact steps and E1/E2/... expectations, observed prerequisites, tool/spec/command/target allowlist, permitted outputs, bounded timeouts/repeat policy, evidence and recovery.
- [ ] Keep execution separate from test authoring/debugging. The executing model cannot edit product/tests/selectors/fixtures, historical results, approved scope or expectations; missing/broken adapters block cases instead of inviting improvisation.
- [ ] Add machine validation outside the model for queue schema, immutable source/scope, exact spec/test allowlists, command/target boundaries, batch budgets and per-expectation evidence completeness. Do not claim prose alone constrains unattended execution.
- [ ] Test boundary scenarios: owner/set mismatch; duplicate IDs; unlisted dependency; missing timeout/evidence; ambiguous selector; unsafe target; ownership loss; denied permission; failed cleanup; sixth batch; hidden retry; attempted context-reset bypass.
- [ ] Persist each case before the next and checkpoint every batch. Record blocked IDs in their original slots; never backfill/reorder dynamically or call a partially tested module PASS.
- [ ] Keep the supervised Markdown fallback until these enforcement checks exist. After one set start, execute only its reviewed batches within budget without approval after each case; stop at the limit and wait for explicit resume, or at any earlier stop condition.

Expected output: larger reviewable module assignments with small deterministic
execution units, a limited executor role and enforceable boundaries independent
of the model's reasoning ability. No agent delegation is started by this plan.

### 3. Migrate catalog parsing and queue tooling

- [ ] Add a shared parser for module headings, `TC-*` cases, E2E step tables, requirements, result notes, run phases and prerequisite tables; choose its module location during implementation.
- [ ] Preserve full procedures/expected results/Notes and relevant global setup. Validate duplicate/malformed IDs, missing blocks, broken requirement mappings and incomplete prerequisites with actionable errors.
- [ ] Treat the current 231 TC and eight E2E counts as the migration baseline; future deliberate catalog additions should require reviewed coverage updates, not silent omission.
- [ ] Remove the queue tool's dependency on the retired renderer and mandatory ISO classification. Support module/phase selection and explicit IDs with owners and selection reasons; optional ISO tags require a reviewed mapping.
- [ ] Define a versioned queue schema and stable JSON/Markdown relationship, adopting the reviewed Markdown contract already documented, including owner/module assignments, immutable batches, session counters, allowlists and complete execution cards. Reject legacy JSON as incompatible rather than silently converting old IDs.
- [ ] Select pending cases using preserved source results and the reviewed historical evidence map. Exclude accepted unchanged historical coverage as well as PASS/FAIL/partial/conflicted entries by default, except explicitly allowed rechecks or verified merged-fix retests. Revalidate reuse decisions against the target revision before selection/start.
- [ ] Reject duplicate names/assignments, unknown or ineligible IDs and empty selections. Never silently substitute cases, add dependencies or broaden a set.
- [ ] Snapshot source revisions/hashes, full case definitions, global dependencies, results, executor, prerequisites, setup/restoration and evidence plans into the reviewed queue.
- [ ] Validate case-card readiness and execution budgets independently of the executing model; reject missing fields, unlisted targets/specs/commands, scope edits and exhausted sessions before live operations.
- [ ] Implement freshness checking before start/resume. Detect relevant procedure, dependency, result and note changes; require a replacement preview/start when scope changes. Preserve completed evidence without adding newly pending cases.
- [ ] Keep preparation read-only with respect to the product, lab and human results. Refuse queue overwrite and keep execution logs separate from immutable reviewed scope.
- [ ] Update `scripts/test_qa_queue.py` with synthetic fixtures and real-catalog validation for both TC/E2E formats, absent result columns, conflicting/free-text results, duplicates, ordering, hashes, resume and selection boundaries.

Expected output: working prepare/show/check commands and tested queue schema for the new suite.
Files: `scripts/qa_queue.py`, shared parser, queue tests, QA guide/workflow.

### 4. Restore documentation and CI verification

- [ ] Update active routing/index links in `AGENTS.md`, `spec files/README.md`, `docs/README.md`, `server/tests/plans/README.md` and QA scope/Playwright documentation to the new catalog.
- [ ] Preserve historical report meaning when repairing old links: point to the historical source revision or archived source, not to an unrelated new case with a similar title.
- [ ] Migrate `scripts/check_traceability.py` to validate the new requirement/case matrix and source references, including E2E coverage where declared.
- [ ] Decide the fate of `scripts/render_qa_case_tables.py`: adapt it to produce an explicitly derived view only if useful, otherwise retire its active invocation. Do not recreate the deleted paper tables solely for the old check.
- [ ] Replace legacy fixture assumptions in `scripts/test_traceability.py`, queue tests and workflow contract tests with meaningful new-source checks; keep regression checks for scope, evidence, safety and stop rules.
- [ ] Align `scripts/verify.sh docs` and CI descriptions/wiring with the supported new checks. Preserve the verification coverage rather than simply removing failing checks.
- [ ] Align `.agent/workflows/fix-found.md` and its contract tests with new-case finding/retest handoff, preserving original failures, real merged-fix proof, duplicate prevention and failed-fix limits.
- [ ] Update `spec files/Agent_Workflow_and_CI.md` and `Implementation_Status.md` to distinguish implemented tooling, remaining gaps and deferred runner work; keep thin skill adapters thin.
- [ ] Run focused parser/queue/traceability/workflow tests, relative-link checks and `git diff --check`, then get `scripts/verify.sh docs` green. Use backend/frontend verification too if implementation touches those areas.
- [ ] For a published implementation PR, confirm required CI checks are green before calling that milestone complete.

Expected output: reproducible green documentation gate without retired-source dependencies.

### 5. Define reports, evidence and retest records

- [ ] Extend `docs/test-runs/TEMPLATE.md` and reporting rules for catalog hash, queue/set, timestamps/time zone, actual deployed app/installer revisions, baseline and executor mode/contributor.
- [ ] Represent PASS, FAIL, PARTIALLY PASS, BLOCKED, Not run and inconclusive explicitly; distinguish unique cases, attempts, setup and completion. Keep TC and E2E totals separate.
- [ ] Require observations for every expected item, per-step E2E results and missing coverage explanations. Mock or intercepted responses cannot certify live acceptance.
- [ ] Define local machine-readable results if scripted execution is selected; derive sanitized summaries rather than independently editing conflicting totals. Include reused-evidence links, accepted target revision and reuse classification separately from new execution timestamps/verdicts.
- [ ] Persist execution/recovery journals and raw evidence outside instances that may be restored. Define sanitization, private storage and evidence references without credentials/cookies/tokens/raw database exports.
- [ ] Verify repeat/retest rules: preserve first failure, repeat only as the approved workflow allows, keep differing outcomes inconclusive, link the same finding and require a real deployed merged fix for retest eligibility.
- [ ] Distinguish the QA workflow's one diagnostic repeat from automatic runner retries. Resolve retry-policy conflicts with the proposed deterministic approach before implementing unattended execution.
- [ ] Define fail/blocked issue handling and report indexing. Retain the same issue-search and installer-ownership rules; no duplicate or fabricated issue links.
- [ ] Test reporting with synthetic pass/fail/partial/blocked/interrupted/cleanup-failure records without creating real product findings.

Expected output: attributable reports that preserve human history and expose incomplete evidence.
Files: report template/rules, result helpers/schema if needed, workflow and tests.

### 6. Prepare and prove the approved lab boundaries

- [ ] Confirm exclusive ownership of the disposable appliance and targets, capacity, endpoints, versions and a restoration baseline; keep shared-environment reservations separate from queue assignment.
- [ ] Choose VM versus isolated Docker per selected case. Do not substitute Docker for installer/systemd/NCPA requirements it cannot prove; do not use the forbidden libvirt harness.
- [ ] Verify VM controller/UUID/runtime endpoint identity through existing preflight. Prove restoration through the actual SSH/HTTP endpoints; snapshot command success alone is insufficient.
- [ ] Identify baseline/setup profiles for fresh first-run tests, normal configured tests, seeded-history cases and E2E. Avoid completing first-run setup before a case that must test it.
- [ ] Provision disposable Super Admin, Staff and limited-permission roles through supported setup paths when authorized. Keep credentials private, isolated and invalidated/recreated after restores; no fallback personal credentials.
- [ ] Verify browser installation/pins, account/session isolation and existing `scripts/playwright-lab` network restrictions. Live credentials must remain within the documented isolated runner, with one worker and no broader egress.
- [ ] Validate selected discovery networks against `10.77.0.0/28` and prohibit overlapping scans. The separate DHCP acceptance exception is not authorization for this suite.
- [ ] Before any unattended scan, implement/prove an enforced guard at scan start that cannot race with configuration changes. A manual read-back alone leaves unattended scan cases blocked; record scan-code scope and applicable backend/data/security specifications before implementation.
- [ ] Declare bounded fault operations, affected targets and restoration before mutation; protect the controlling connection and preserve an independent recovery path where SSH/service interruption is tested.
- [ ] Verify SMTP/inbox access and delivery evidence for selected email cases, SNMP targets, NCPA-capable guests and needed monitoring/history data. Mark unavailable capabilities blocked rather than replacing required observations.
- [ ] Define timeouts, cancellation, interruption/resume, lab lock/claim handling and cleanup failure behavior. Failed restoration stops further shared-lab mutation until recovered.
- [ ] Require explicit set start before performing these live preparations or proofs. Preparation commands in documentation are not authorization to execute them during planning.

Expected output: recorded preflight/baseline/restoration evidence for the selected environment.
Files: lab/run configuration, existing vmlab/Playwright helpers and safety tests as needed.

### 7. Implement the chosen execution coverage

- [ ] Reuse existing `client/e2e/` specs and fixtures where their assertions match the new cases. Map coverage explicitly; a smoke test or old title does not prove an entire new case.
- [ ] For AI-assisted runs, provide case-level operating instructions, bounded observations and stop conditions; record the actual agent/human actions instead of claiming deterministic automation.
- [ ] For scripted runs, implement browser/API tests for selected cases using stable accessible selectors, separate sessions and complete expected-result assertions. Use API actions only where the case permits them; shell operations are fixtures/fault injection, not replacements for UI workflows.
- [ ] Add dependency-aware sequential orchestration, bounded polling, fresh-state evidence, cancellation, durable journal and verified cleanup for unattended scope. Do not silently repair the product, fabricate records, fulfil live API responses with mocks or rescue failed application reloads manually to gain a pass.
- [ ] Reconcile the older deterministic-runner proposal against current source/specs before adopting it. Do not implement obsolete UI/API proposals or its forbidden harness merely because they appear in that deferred plan.
- [ ] Test the harness itself for stale observations, unavailable prerequisites, credential failure, network rejection, interruption, partial evidence, dependency blocking and cleanup failure using isolated fixtures first.
- [ ] Keep human-assisted and unsupported cases visible outside unattended coverage. An eligible AI-assisted case does not automatically qualify for unattended execution.

Expected output: executable coverage and recovery for the reviewed subset, with truthful coverage mapping.

### 8. Review and start a pilot, then expand

- [ ] Choose a small representative pilot after eligibility/environment review: a safe browser flow, a permission/negative case and a reversible state change. Name exact IDs only after confirming prerequisites and result history.
- [ ] Prepare its fixed queue with owner/module mapping, ordered batches and exact tool/spec/command selections; show full cases, prior human results, selection reasons, executor, setup, evidence, restoration, timeouts and remaining decisions.
- [ ] Obtain an explicit start for that queue/set. A go signal to implement this readiness plan does not automatically start product testing.
- [ ] Execute the pilot, retain failures, verify cleanup and publish only authorized sanitized report/index/queue updates. Address harness defects separately from product defects.
- [ ] If unattended execution is the target, demonstrate two consecutive authorized runs of the same supported case set from the same verified baseline with consistent classifications and no prompts, AI repairs or hidden omissions. Consistent product failures remain failures.
- [ ] Review pilot results and readiness gaps before expanding module by module in dependency order. Keep disruptive/fresh-appliance cases in their documented phases and E2E on its required baseline.
- [ ] Prepare each later queue/set for review/start. Do not automatically drain all 239 cases/scenarios or claim full-suite acceptance from pilot success.

Expected output: demonstrated readiness for a defined scope, followed by separately approved expansion.

## Gates

| Gate | Required before proceeding | Evidence |
|---|---|---|
| Implementation | User's go signal for readiness work | Explicit user instruction; issue/checkout/progress established afterwards |
| Queue preparation tooling complete | Phases 1–4 including historical-evidence review implemented and verified | New-catalog CLI/tests, correct migration, green docs gate |
| Pilot may start | Selected cases resolved; phases 5–7 ready for that scope; reviewed queue and lab ownership | Exact case/executor/evidence/restoration plan plus explicit set start |
| Unattended cases may start | Deterministic runner and recovery, enforced boundaries including scan guard if scans occur, no required human observation during the run | Harness tests and approved unattended scope/start |
| Expand beyond pilot | Pilot results and restoration reviewed; remaining blockers visible | Attributable report, coverage matrix and next reviewed queue |

Known product failures do not have to be fixed to test the system. They must remain
visible, with intentional diagnostic/retest scope. Unknown expectations, unsafe
execution and missing mandatory evidence block the affected cases.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| Offline implementation #206 | Parser/queues/evidence/session validation and documentation migration implemented in the isolated issue checkout | `scripts/verify.sh docs` and syntax/whitespace checks | Green: 4310 backend/1003 frontend plus build/lint; draft PR #207 published, final-head CI to inspect; live readiness remains pending |
| Batch/guardrail documentation | Updated QA workflow/guide and owning specifications for owner/module assignments, up to 25 ordinary cases in five fixed batches, execution cards and explicit stop actions; added independent-enforcement tasks here | Nine fix-found contracts; one queue workflow contract; changed-document link/guardrail assertions; `git diff --check`; `scripts/verify.sh docs` | Focused checks passed; full docs gate still blocked by the same 11 legacy links. Documentation only; no implementation or live QA started |
| Tool-stack planning | Added explicit tool-by-test-type matrix, AI execution flow, existing versus planned capability, exact selection, retry and artifact-isolation tasks | Plan local-link/tool-stack assertions and `git diff --check` | Passed; planning only, no implementation or test execution |
| Evidence-reuse planning | Added provisional October 15 cutoff, case-to-report matching, version/impact review, separate reused-coverage totals and rerun triggers; no mapping accepted or case executed | Updated-plan local-link/policy assertions and `git diff --check` | Passed; planning only |
| Planning | Created this readiness checklist only; implementation and live execution await approval | Plan structure/local-link assertions; `git diff --check`; `scripts/verify.sh docs` | Plan checks and whitespace passed; full docs gate blocked by the same 11 existing links to removed QA documents. No product testing performed. |

## State for the next session

- Last check run: `scripts/verify.sh all` (green), followed by final `scripts/verify.sh docs` (66 isolated checks) for QA-only hardening.
- Result: 4310 backend tests passed (14 skips), 1003 frontend tests passed, build and lint passed with zero errors. Offline milestone is in draft PR #207; inspect its final-head CI. No live cases have been executed.
- Next action: Continue current-case adapter/coverage preparation from this checklist after reviewing #207. Live preflight/scan guard/recovery and the pilot still require their reviewed scope/start. Human-result conflicts and the provisional cutoff remain explicit review items.


## Decisions and notes

- This descriptive file is the overall readiness checklist. Authorized offline implementation now uses the real issue-scoped progress file for #206.
- Version-2 JSON queues with generated Markdown previews have replaced the manual Markdown fallback. Incomplete execution cards remain blocked.
- Do not resolve human-result conflicts, add ISO classifications or change product expectations by assumption.
- Human evidence requirements are case-specific. Do not block an independent pilot solely because an unrelated case needs a person, but never claim those omitted cases passed.
- This plan is local scaffolding for review, not a published design or authorization to operate the lab.

- Historical evidence reuse is requested. The October 15 cutoff is a recommendation pending review; report attachment is required, and coverage plus version compatibility determine whether rerunning can be avoided.
