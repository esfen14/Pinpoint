# AI automated testing readiness plan

Date: 2026-10-18 (Asia/Manila)
State: Narrow pilot driver/card and read-only preflight complete; explicit acceptance start pending (#206)
Tracking issue: [#206](https://github.com/esfen14/Pinpoint/issues/206); issue-scoped progress is [issue-206.md](issue-206.md).
Current authorization: implement readiness tooling in the isolated issue checkout.
The later user instruction authorized access to the exclusive local VirtualBox
appliance, followed by explicit backup/deployment/migration/restart/Staff setup
approval. Those setup operations are complete and documented below. Actual case
execution, fault injection, snapshot restore and new scans remain unauthorized.
An existing automatic startup scan is disclosed in the preparation report.

## Finish condition

This checklist defines readiness to execute the new black-box cases. It does not
claim that the product passes or that every case can run without human involvement.

- [x] The new catalog, historical human results and new execution records have clear, validated ownership.
- [x] Queue preparation/checking and the documentation gate work against the new catalog without restoring retired inputs.
- [x] Investigate current human partials, attach issue/disposition links and preserve original results; follow-up remains in #208/#209 and the [partial-pass register](https://github.com/esfen14/Pinpoint/blob/issue-206-qa-readiness/docs/qa/Partial_Pass_Investigations.md).
- [x] Implement and synthetically test the supervisor lifecycle core: separate start identity, cooperative UUID lock, durable pre-dispatch action consumption, replay/budget persistence and halted interruption/cleanup handling (16 isolated contracts).
- [x] Implement/test bounded local process-group control and strict permission-report parsing (8 local-process and 9 synthetic-report contracts), retaining private evidence and inconclusive outcomes.
- [x] Coordinate supervisor and mutating VM-controller entries with one private per-user host claim; verify inherited descriptors and cross-ledger exclusion using local fixtures. Collect structured host-only observations without asserting deployment readiness.
- [x] Implement/test concrete pinned-image container creation, identity/isolation verification, bounded attach and owned-resource removal/absence with durable intent and consumed-transport binding (16 synthetic contracts); fix worker config reload using 7 offline frontend helper checks.
- [x] Implement and fixture-test the owned private bridge (11 Unix-only contracts), container custody integration (16 contracts) and standalone Git/artifact/process observer (6 contracts); observed disk/process facts remain separate from actual running/served identity.
- [x] Complete authorized appliance setup: consistent verified backups, exact-target build/deployment/migrations, Staff initialization and served-artifact checks; disclose startup scan and preserve temporary scheduler pause.
- [x] Integrate the narrow TC-SS-04 production driver, controlled launch/build provenance and fresh actual proof checks; pass eleven composed contracts and supported read-only inspection.
- [ ] Prove actual browser/container execution and session/resource/baseline cleanup in the explicitly started pilot; broader/unattended integration remains open.
- [x] The selected initial TC-SS-04 pilot has an unambiguous expectation, executor, observed prerequisites, evidence paths and written cleanup/stop procedure.
- [x] TC-SS-04 maps to its exact reviewed tool/spec/project/title/assertion and private evidence output; other case mappings remain separately pending.
- [ ] Historical runs have been mapped to current expectations with linked evidence, an agreed cutoff and a version/impact check; only uncovered or invalidated coverage enters the new-execution queue.
- [ ] The selected lab and automation tools enforce the approved boundaries and fail closed when those boundaries cannot be proved.
- [x] The complete v4 one-case pilot queue/card is ready for its first supervised attempt; separate user start is pending, actual live cleanup unverified.
- [ ] After a separate explicit start, the pilot demonstrates execution, reporting, failure handling and verified restoration.
- [ ] Unattended testing is enabled only for cases with deterministic execution and recovery; remaining cases stay explicitly human-assisted or blocked.

## Implemented offline milestone

- Shared parser validates all 231 TC/eight E2E procedures, phases and requirements;
  conflicting human results remain flagged.
- Queue v2 supports module/person assignments, fixed batches, exact IDs, exclusions,
  source snapshots/freshness, optional cards and reviewer-bound historical reuse.
- Forty-one post-cutoff-directory-date reports are inventoried; six current-case
  mappings are partial. No inherited full-case PASS or cutoff decision is invented.
- All 239 definitions now have explicit source-coverage records: five Staff permission adapters implemented in source, 234 unmapped. Registry and queue/card binding reject changed sources, incomplete coverage and broader selections.
- The separate Playwright config has exact IDs, no setup dependency/retry/capture, one worker and private unique artifacts. Type checks and five offline collection/selection tests pass. An offline queue/journal-bound transport preview now defines the private environment/mount contract and rejects legacy live fallthrough. A synthetic-driver supervisor lifecycle core now validates durable sequencing and halted recovery states. Production supervision and all live cards remain blocked; no browser was launched.
- Offline session validation rejects missing owner/start/preflight attestations,
  incomplete/changed adapters, wrong action slots, exhausted budgets, incomplete
  PASS evidence and failed cleanup. It dispatches no live commands and is not an
  OS sandbox. Live adapter completion, preflight, enforced scan guard, recovery/resume
  and pilot runs remain separate pending work.
- Current/historical links and docs checks have migrated. `scripts/verify.sh docs`
  is green (118 isolated checks). The prior full local baseline passed 4310
  backend/1003 frontend tests plus build/lint. The later combined run passed backend
  but hit intermittent frontend test #210; focused and full frontend stage reruns
  passed. No clean latest combined-run result is inferred from those stage reruns. [Draft PR #207](https://github.com/esfen14/Pinpoint/pull/207)
  contains the offline milestone; final-head CI is checked separately.

Checklist audit: completed items below are checked against the implementation in
[PR #207](https://github.com/esfen14/Pinpoint/pull/207), source files and isolated
checks. Aggregate items are split where only the offline portion is implemented.
Unchecked items remain work to do; no live case execution or unattended readiness
is claimed. The main checkout receives a copy of this plan for visibility; the
implementation and validation live in `../Network-Diagnosis-System-qa-readiness`.

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
| Case selection and historical evidence reuse | Python standard-library catalog parser, migrated `scripts/qa_queue.py` and reviewed case-to-report map | Produce/check fixed case sets and exclude accepted unchanged historical coverage | Implemented: shared parser, queue v2 and reviewer-bound reuse validation. Actual accepted target-build coverage remains pending. |
| Result collection and reporting | Playwright JSON output; Python report/evidence processing; `scripts/new_test_run.sh` | Unique per-run raw artifact directory outside restored guests; sanitized `docs/test-runs/.../REPORT.md`, index and queue log | Report template/rules and offline JSON journal include executor, queue/session, expected-item observations and distinct historical credit. Automated sanitized summary generation and run-specific Playwright artifact routing remain pending. |
| Unattended orchestration | A small Python controller around existing queue, lab and Playwright tools | Validate manifest, hold one lab lock, execute dependencies sequentially, journal interruption, recover and finalize a complete report | `scripts/qa_execute.py` exists as an offline-only journal/card/result validator. Live dispatch, lock enforcement, recovery/resume and automatic report generation are not implemented. |
| Implementation regression checks | `scripts/verify.sh docs/backend/frontend/all` using existing standard-library checks, pytest, Vitest, TypeScript build and lint | Verify changes to tooling or product code as applicable | Exists; new-catalog docs migration passes. These checks verify implementation, not live black-box acceptance. |

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
- [x] Verify actual VirtualBox/Node/Python, private credentials, Docker image availability and pinned cached Chromium binary during authorized read-only preflight. The pilot uses the owned bridge and Node proxy, with no socat dependency.
- [ ] Prove actual container Chromium/library loading and owned Unix bridge/resource/session cleanup during the explicitly started pilot.
- [ ] Add a case-to-tool/spec/project mapping for every selected ID, including required fixtures, assertion method, evidence output and cleanup. Record reuse rather than claiming every existing spec covers the new case in full.
- [x] Bind reviewed source mappings/cards to exact file, title, project, config and command; reject unmapped/partial or stale mappings. Offline collection proves one-case/five-case selection with no old setup projects.
- [x] Add an offline queue/journal-bound transport preview with exact selection, private non-overwriting evidence mounts, read-only source/root, minimal Staff credential exposure and rejected legacy launch fallthrough.
- [x] Implement and test the driver-independent supervisor lifecycle: bound separate grant, cooperative lab lock, fresh receipt validation, fsynced consumption, persistent budgets and halted failures.
- [x] Connect the narrow no-network pilot driver, actual controlled baseline/served proof, inherited host claim, durable consumption, cancellation/result/cleanup wiring; retain no automatic retry/resume.
- [ ] Validate actual container/browser operation and recovery in the explicit pilot; extend other case types only after reviewed mappings.
- [x] Add a dedicated current-case configuration with one worker, zero retries even under CI, no setup dependencies and no default selection; verify with offline collection.
- [ ] Prove the reviewed live launcher preserves those limits and separate diagnostic attempts; the legacy config still has different retry behavior and is not inherited by this adapter configuration.
- [ ] Persist unique run-specific JSON/download/journal outputs before reset or another launch; the current single `playwright-results.json` path must not overwrite earlier run evidence.
- [ ] Keep login trace/video/screenshot capture disabled. Capture only authorized non-secret evidence after login, sanitize reports and never publish raw auth state or credential-bearing artifacts.
- [x] Prove narrow pilot fixture/runner/cleanup failure handling with eleven isolated composed-driver contracts before approved live use. Mark human-dependent or unmapped cases blocked instead of switching to an unreviewed tool.

## Plan

Complete phases in order. Items may be implemented together when they share the
same contract. Implementation approval does not automatically start a live queue;
the saved queue/set still needs its explicit start under the QA workflow.

### 1. Establish the approved source and execution model

- [x] After the go signal, establish a real tracking issue and dedicated implementation checkout/branch; use an issue-scoped progress file without mixing owner changes into the work.
- [x] Freeze the catalog revision/content hash, review the existing deletions and identify which source changes belong in the migration.
- [x] Document the existing TypeScript Playwright/Chromium stack and separate AI-assisted exploration from scripted automation; implement shared catalog/queue/reporting support as the offline first milestone. Runtime validation and the scripted pilot remain open below.
- [x] Inventory all live references to the retired documents, old case IDs and ISO queue assumptions across `.agent/`, skill/command adapters, `scripts/`, `docs/`, `spec files/`, `AGENTS.md`, client E2E specs and CI.
- [x] Keep historical journey reports and their original IDs/results intact. Use an archived source revision for historical links where needed; do not remap historical evidence to new case IDs without review.
- [x] Establish ownership: catalog = procedures/requirements plus preserved human history; run reports = new observed executions; queues = reviewed assignments/eligibility. Decide whether a derived current-status view is useful; never create competing editable ledgers.

Expected output: agreed source/result contract and migration scope.
Files: current catalog, QA workflow/guide, tracking progress, owning workflow/status specifications.

### 2. Reconcile eligibility and make selected cases executable

- [x] Recount and list summary/detail conflicts by ID, copying both human entries and observations into a decision record.
- [ ] Obtain the human tester's clarification where possible. Preserve original observations and record who resolved each conflict and why; never infer missing tester/date/SHA/evidence.
- [x] Keep unresolved cases `needs-decision` and exclude them from ordinary pending queues. An explicitly approved diagnostic recheck may gather new evidence without changing the old result.
- [x] Handle EDG/SEQ tables that have no Result column using detailed Result lines; distinguish absent columns, missing verdicts, free-text notes and explicit Not run.
- [x] Investigate both catalog partials and search existing issues; link attributed defect #208 and evidence clarification #209 in the [partial-pass register](https://github.com/esfen14/Pinpoint/blob/issue-206-qa-readiness/docs/qa/Partial_Pass_Investigations.md). No fresh runtime reproduction is claimed.
- [ ] Finish issue/disposition review for the four recorded failures and unclassified acknowledgement-filter observation. Resolve TC-REM-04's missing observation and obtain live verification where required.
- [ ] Check selected expectations against behavioral specifications and team decisions. Document app/spec conflicts rather than weakening the case to match current behavior.
- [ ] Specify exact timing boundaries, clocks, target counts/load, polling limits, warm/cold assumptions and sampling rules for NFR cases. Preserve specified thresholds; ask for decisions on undefined rules.
- [ ] Define state-based prerequisites and concrete setup data for selected cases: accounts/permissions, hosts/services, active incidents, identity candidates, SNMP devices, deployed NCPA agents and sufficient history.
- [ ] Classify each selected case as AI-assisted, scripted, human manual or mixed. Identify external inbox checks, subjective usability observations, installer steps and inaccessible targets that need a person or additional fixtures.
- [x] Publish a validated all-case source-coverage matrix: 239 entries, five source-complete adapters and 234 explicitly unmapped records with missing expected items.
- [ ] Finish executor/fixture classification for unmapped cases and resolve the selected pilot scope; an unmapped entry is an accounting placeholder, not an automation assessment or live readiness.

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
- [x] Inventory 41 reports with post-cutoff directory dates in `docs/qa/historical-report-inventory.json`; retain report links/hashes and provisional candidate status.
- [ ] Finish execution-time/provenance review of inventory candidates: actual app/installer SHA, executor, environment, observations and limitations. Directory dates alone do not establish eligible execution dates.
- [ ] Keep pre-cutoff evidence as background or defect history by default. An exception needs explicit rationale/review and the same full coverage/version checks; do not automatically import old passes.
- [x] Attach six provisional current-case mappings to the October 17 issue-182 report with report/case hashes and scope limitations in `docs/qa/historical-evidence-review.json`. None confers a whole-case PASS.
- [ ] Complete behavior/item-level mappings for the remaining applicable reports, with exact row references, covered/missing expectations and target-build compatibility review.
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
document this contract. Queue preparation and offline validation are implemented; live enforcement and actual reviewed assignments remain pending.

- [ ] Prepare owner-to-module assignments and expand each to fixed eligible IDs after evidence review. Show exclusions, conflicts and accepted historical coverage; do not allocate the same case to multiple owners.
- [ ] Verify each person's own appliance AND targets or agree on exclusive access windows. Module ownership does not reserve the lab or establish another module's prerequisites.
- [x] Partition each set into fixed ordered batches of at most five ordinary TC IDs. Isolate every E2E, disruptive/fault, fresh-appliance or long case in a single-case batch, following catalog phases.
- [x] Enforce a five-batch limit in persisted offline journals, consuming budget on opening a batch and rejecting reuse/sixth batches. Isolated tests include five actual blocked batches.
- [ ] Prove interruption/handoff/context-reset and explicit-resume behavior in live orchestration; offline journals alone cannot prevent a model with arbitrary file access from creating another journal.
- [x] Make the selected TC-SS-04 execution card complete before start: source/target versions, exact steps and E1/E2/... expectations, observed prerequisites, tool/spec/command/target allowlist, permitted outputs, bounded timeouts/repeat policy, evidence and recovery.
- [x] Document the executor's prohibition on product/test/scope edits; offline validation rejects changed adapters, missing cards and out-of-order actions.
- [ ] Enforce and prove that separation in the live launcher/process permissions; documented restrictions and content hashes are not an OS sandbox.
- [x] Add offline machine validation for queue identity/schema, owner/start attestations, card/adapter hashes, exact action argv slots, ordered batch budgets, evidence completeness and cleanup halts.
- [ ] Implement live command/spec/target/network boundaries, exclusive lab ownership and recovery enforcement outside the executing model.
- [ ] Test boundary scenarios: owner/set mismatch; duplicate IDs; unlisted dependency; missing timeout/evidence; ambiguous selector; unsafe target; ownership loss; denied permission; failed cleanup; sixth batch; hidden retry; attempted context-reset bypass.
- [ ] Persist each case before the next and checkpoint every batch. Record blocked IDs in their original slots; never backfill/reorder dynamically or call a partially tested module PASS.
- [ ] Keep the supervised Markdown fallback until these enforcement checks exist. After one set start, execute only its reviewed batches within budget without approval after each case; stop at the limit and wait for explicit resume, or at any earlier stop condition.

Expected output: larger reviewable module assignments with small deterministic
execution units, a limited executor role and enforceable boundaries independent
of the model's reasoning ability. No agent delegation is started by this plan.

### 3. Migrate catalog parsing and queue tooling

- [x] Add a shared parser for module headings, `TC-*` cases, E2E step tables, requirements, result notes, run phases and prerequisite tables; choose its module location during implementation.
- [x] Preserve full procedures/expected results/Notes and relevant global setup. Validate duplicate/malformed IDs, missing blocks, broken requirement mappings and incomplete prerequisites with actionable errors.
- [x] Treat the current 231 TC and eight E2E counts as the migration baseline; future deliberate catalog additions should require reviewed coverage updates, not silent omission.
- [x] Remove the retired-renderer/mandatory-ISO dependency; support module selectors and explicit IDs with owners and exclusion reasons in queue v2. Run-phase metadata controls catalog order and singleton batching.
- [ ] Add an explicit phase selector if required; the CLI currently accepts module/case selectors only. Optional ISO tags still need a reviewed mapping.
- [x] Implement queue v2 JSON/Markdown previews with owner/module assignments, immutable batches, source snapshots and optional execution cards; reject legacy JSON. Offline session journals track batch budgets.
- [x] Complete the selected TC-SS-04 card/allowlist and initial-attempt start/consumption path; all older empty-card drafts stay superseded/blocked.
- [ ] Prove actual live session cleanup and interruption/recovery before extending resume support; no automatic resume exists.
- [x] Select pending cases using preserved source results and the reviewed historical evidence map. Exclude accepted unchanged historical coverage as well as PASS/FAIL/partial/conflicted entries by default, except explicitly allowed rechecks or verified merged-fix retests. Revalidate reuse decisions against the target revision before selection/start.
- [x] Reject duplicate names/assignments, unknown or ineligible IDs and empty selections. Never silently substitute cases, add dependencies or broaden a set.
- [x] Snapshot source/target revisions, hashes, full case definitions, global dependencies, original results and supplied execution metadata into immutable queue scope.
- [ ] Supply and review actual selected-case executor, prerequisites, setup/restoration and evidence cards; empty cards remain blocked.
- [ ] Validate case-card readiness and execution budgets independently of the executing model; reject missing fields, unlisted targets/specs/commands, scope edits and exhausted sessions before live operations.
- [x] Detect changed case definitions, results, notes, normative/harness sources and accepted evidence; require replacement review without adding newly eligible cases. The offline CLI checks freshness before journal operations.
- [ ] Implement and prove freshness/ownership checks in the live resume dispatcher; no dispatcher exists yet.
- [x] Keep preparation read-only with respect to the product, lab and human results. Refuse queue overwrite and keep execution logs separate from immutable reviewed scope.
- [x] Add synthetic/real-catalog regressions across parser, queue, evidence and offline executor tests for TC/E2E definitions, absent/conflicting results, duplicate assignments, ordering, hashes, selection, adapter/evidence rejection and batch limits.
- [ ] Add live resume/interruption boundary tests when the dispatcher and recovery implementation exist.

Expected output: working prepare/show/check commands and tested queue schema for the new suite.
Files: `scripts/qa_queue.py`, shared parser, queue tests, QA guide/workflow.

### 4. Restore documentation and CI verification

- [x] Update active routing/index links in `AGENTS.md`, `spec files/README.md`, `docs/README.md`, `server/tests/plans/README.md` and QA scope/Playwright documentation to the new catalog.
- [x] Preserve historical report meaning when repairing old links: point to the historical source revision or archived source, not to an unrelated new case with a similar title.
- [x] Migrate `scripts/check_traceability.py` to validate the new requirement/case matrix and source references, including E2E coverage where declared.
- [x] Decide the fate of `scripts/render_qa_case_tables.py`: adapt it to produce an explicitly derived view only if useful, otherwise retire its active invocation. Do not recreate the deleted paper tables solely for the old check.
- [x] Replace legacy fixture assumptions in `scripts/test_traceability.py`, queue tests and workflow contract tests with meaningful new-source checks; keep regression checks for scope, evidence, safety and stop rules.
- [x] Align `scripts/verify.sh docs` and CI descriptions/wiring with the supported new checks. Preserve the verification coverage rather than simply removing failing checks.
- [x] Align `.agent/workflows/fix-found.md` and its contract tests with new-case finding/retest handoff, preserving original failures, real merged-fix proof, duplicate prevention and failed-fix limits.
- [x] Update `spec files/Agent_Workflow_and_CI.md` and `Implementation_Status.md` to distinguish implemented tooling, remaining gaps and deferred runner work; keep thin skill adapters thin.
- [x] Run focused parser/queue/traceability/workflow tests, relative-link checks and `git diff --check`, then get `scripts/verify.sh docs` green. Use backend/frontend verification too if implementation touches those areas.
- [ ] For a published implementation PR, confirm required CI checks are green before calling that milestone complete.

Expected output: reproducible green documentation gate without retired-source dependencies.

### 5. Define reports, evidence and retest records

- [x] Extend `docs/test-runs/TEMPLATE.md` and reporting rules for catalog hash, queue/set, timestamps/time zone, actual deployed app/installer revisions, baseline and executor mode/contributor.
- [x] Represent PASS, FAIL, PARTIALLY PASS, BLOCKED, Not run and inconclusive explicitly; distinguish unique cases, attempts, setup and completion. Keep TC and E2E totals separate.
- [x] Require observations for every expected item, per-step E2E results and missing coverage explanations. Mock or intercepted responses cannot certify live acceptance.
- [x] Implement strict machine-readable import for the five permission adapters: exact non-retried selection, private fresh report/item attachments, fixed sanitized observations and explicit inconclusive/cleanup state.
- [ ] Integrate result import into the production driver/report index, complete structured failed-item evidence and derived suite/reuse totals, and prove live provenance. Partial parser coverage is not full-suite reporting readiness.
- [ ] Persist execution/recovery journals and raw evidence outside instances that may be restored. Define sanitization, private storage and evidence references without credentials/cookies/tokens/raw database exports.
- [x] Verify repeat/retest rules: preserve first failure, repeat only as the approved workflow allows, keep differing outcomes inconclusive, link the same finding and require a real deployed merged fix for retest eligibility.
- [ ] Distinguish the QA workflow's one diagnostic repeat from automatic runner retries. Resolve retry-policy conflicts with the proposed deterministic approach before implementing unattended execution.
- [x] Define fail/blocked issue handling and report indexing. Retain the same issue-search and installer-ownership rules; no duplicate or fabricated issue links.
- [ ] Test reporting with synthetic pass/fail/partial/blocked/interrupted/cleanup-failure records without creating real product findings.

Expected output: attributable reports that preserve human history and expose incomplete evidence.
Files: report template/rules, result helpers/schema if needed, workflow and tests.

### 6. Prepare and prove the approved lab boundaries

- [ ] Confirm exclusive ownership of the disposable appliance and targets, capacity, endpoints, versions and a restoration baseline; keep shared-environment reservations separate from queue assignment.
- [ ] Choose VM versus isolated Docker per selected case. Do not substitute Docker for installer/systemd/NCPA requirements it cannot prove; do not use the forbidden libvirt harness.
- [x] Verify actual VM/controller/UUID/runtime forwarding through host preflight and controlled deployed target through SSH/HTTP.
- [ ] Prove restoration through actual SSH/HTTP endpoints for cases that need it; no snapshot restore was performed or authorized for this permission pilot.
- [ ] Identify baseline/setup profiles for fresh first-run tests, normal configured tests, seeded-history cases and E2E. Avoid completing first-run setup before a case that must test it.
- [x] Provision and initialize the disposable zero-permission Staff user through supported setup paths; close its setup sessions.
- [ ] Provision additional Super Admin/limited-permission fixtures for other cases when authorized. Keep credentials private, isolated and invalidated/recreated after restores; no fallback personal credentials.
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
- [x] Implement source adapters for TC-SS-04, TC-HIS-01, TC-RPT-07, TC-LOG-05 and TC-PLG-07 with UI sign-in, independent contexts, every written expected item, sanitized observations and logout verification.
- [ ] Implement remaining selected-case adapters and prove live behavior on the reviewed environment. Existing human PASS cases are still excluded unless intentionally rechecked.
- [ ] Add dependency-aware sequential orchestration, bounded polling, fresh-state evidence, cancellation, durable journal and verified cleanup for unattended scope. Do not silently repair the product, fabricate records, fulfil live API responses with mocks or rescue failed application reloads manually to gain a pass.
- [ ] Reconcile the older deterministic-runner proposal against current source/specs before adopting it. Do not implement obsolete UI/API proposals or its forbidden harness merely because they appear in that deferred plan.
- [x] Test coverage/card source drift, broadened commands, missing expected items, unmapped/draft cards, private output paths, exact collection and incomplete action history with isolated fixtures.
- [ ] Finish harness coverage for actual live credential/network failures, interrupted dispatch, lab-claim loss, restoration/resume and stale monitoring observations before live/unattended use.
- [ ] Keep human-assisted and unsupported cases visible outside unattended coverage. An eligible AI-assisted case does not automatically qualify for unattended execution.

Expected output: executable coverage and recovery for the reviewed subset, with truthful coverage mapping.

### 8. Review and start a pilot, then expand

- [x] Choose TC-SS-04 as the initial safe permission/browser pilot after eligibility/environment review; exact one-case v4 scope excludes inherited PASS reruns.
- [ ] Expand representative coverage to a reversible state change and other journeys only after initial pilot review and separately reviewed scope.
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
| Owned bridge/observations | Added consumed-slot/retained-lock private relay, container custody checks and standalone Git/artifact/process observations | 11 Unix-only bridge, 16 synthetic container and 6 disposable deployment-observer contracts; docs gate | No lab/SSH/HTTP/Docker/browser; runtime/served identity, driver/card/recovery remain pending |
| Same-day pilot components | Added concrete pinned/consumed Docker lifecycle and fixed real worker reload in a synthetic no-browser fixture; TC-SS-04 selected | 13 synthetic container contracts; full frontend gate with 7 helper checks and 1003 product tests | User explicitly chose offline preparation; no live preflight, Docker daemon or acceptance run |
| Shared host control | Added fixed per-user supervisor/controller claim and structured read-only host observations; running application identity remains unproved | Six lock/controller fixtures, seven new observation contracts and cross-ledger supervisor regression; docs gate | No live tools; inherited production driver wiring, deployment/baseline/recovery proof remain pending |
| Runtime process/results | Added allowlisted bounded process groups, private output and strict one-case result parser; bootstrap private umask | Eight local-process/nine synthetic-report tests plus docs gate | No live tools; production proof/driver/container lifecycle/recovery remain pending |
| Supervisor lifecycle core | Added separate grant/receipt checks, shared private OS lock/ledger, durable consumption and halt/replay/budget/result enforcement; production driver stays absent | Fifteen synthetic-driver regressions plus docs gate | Verification recorded in issue progress; no live tools or operations |
| Transport preparation | Added offline queue/journal-bound minimal container preview, private mount/credential metadata guards and blocked legacy current-case fallthrough | Nine synthetic transport checks, docs gate and shell syntax/whitespace | Local verification recorded in issue progress; no credential values, live socket, Docker, browser or lab operation |
| Coverage/adapters implementation | Added all-case source registry, five permission adapters, exact offline collection/private artifacts and queue/card source binding; draft cards fail closed | Docs gate (77 isolated checks), frontend gate (1003 existing tests plus five Node checks), QA type check | Green locally; full verification and final-head CI recorded separately; no browser/lab execution |
| Checklist audit | Checked verified offline substeps, split partial aggregates and retained open case mapping, reuse approval, live enforcement and pilot requirements; synchronize main-checkout plan | Source/test/report review; `scripts/verify.sh docs`; final-head CI review | Docs gate passed (68 isolated checks); no live QA |
| Offline implementation #206 | Parser/queues/evidence/session validation and documentation migration implemented in the isolated issue checkout | `scripts/verify.sh docs` and syntax/whitespace checks | Green: 4310 backend/1003 frontend plus build/lint; draft PR #207 published, final-head CI to inspect; live readiness remains pending |
| Batch/guardrail documentation | Updated QA workflow/guide and owning specifications for owner/module assignments, up to 25 ordinary cases in five fixed batches, execution cards and explicit stop actions; added independent-enforcement tasks here | Nine fix-found contracts; one queue workflow contract; changed-document link/guardrail assertions; `git diff --check`; `scripts/verify.sh docs` | Focused checks passed; full docs gate still blocked by the same 11 legacy links. Documentation only; no implementation or live QA started |
| Tool-stack planning | Added explicit tool-by-test-type matrix, AI execution flow, existing versus planned capability, exact selection, retry and artifact-isolation tasks | Plan local-link/tool-stack assertions and `git diff --check` | Passed; planning only, no implementation or test execution |
| Evidence-reuse planning | Added provisional October 15 cutoff, case-to-report matching, version/impact review, separate reused-coverage totals and rerun triggers; no mapping accepted or case executed | Updated-plan local-link/policy assertions and `git diff --check` | Passed; planning only |
| Planning | Created this readiness checklist only; implementation and live execution await approval | Plan structure/local-link assertions; `git diff --check`; `scripts/verify.sh docs` | Plan checks and whitespace passed; full docs gate blocked by the same 11 existing links to removed QA documents. No product testing performed. |

## State for the next session

- Narrow pilot driver/card and actual supported read-only inspection are complete; docs gate passes 176 isolated contracts. No local backend or unchanged frontend suite rerun. No acceptance case/batch/browser/container/bridge started.
- Next action: obtain explicit user start for `docs/qa/queues/2026-10-18-today-ss04-v4.json`, set `today-ss04`, Paeng, one initial TC-SS-04 attempt. Only then write the matching affirmative expiring private grant and execute its exact launcher command. Preserve false template until actual approval.
- After that attempt, verify actual session/container/bridge/baseline cleanup and publish a separate acceptance report; stop on uncertainty or INCONCLUSIVE, with no automatic repeat, reset, restore, scheduler enable or alternate browser/tool. The VM remains running with scheduler off and private backup retained; reboot invalidates baseline.

## Decisions and notes

- This descriptive file is the overall readiness checklist. Authorized offline implementation now uses the real issue-scoped progress file for #206.
- Version-2 JSON queues with generated Markdown previews have replaced the manual Markdown fallback. Incomplete execution cards remain blocked.
- Do not resolve human-result conflicts, add ISO classifications or change product expectations by assumption.
- Human evidence requirements are case-specific. Do not block an independent pilot solely because an unrelated case needs a person, but never claim those omitted cases passed.
- This plan is local scaffolding for review, not a published design or authorization to operate the lab.

- Historical evidence reuse is requested. The October 15 cutoff is a recommendation pending review; report attachment is required, and coverage plus version compatibility determine whether rerunning can be avoided.

Verification instruction (user, 2026-10-18): skip backend test runs on subsequent
passes when application backend code is unchanged. Run focused QA tooling checks,
the docs gate and relevant frontend checks. Existing GitHub CI may still schedule
a backend job automatically; do not claim that job passed or change CI policy
without an actual result. No local backend suite is needed for this change.

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
- [ ] Obtain explicit acceptance start and verify actual browser/container/session cleanup in the pilot.

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
- [ ] Obtain the user's explicit start for v4 `today-ss04`, Paeng; only then create the matching affirmative expiring private start record. Current template is false/expired. No acceptance case, batch, browser, container or bridge started.
- [ ] Perform first supervised TC-SS-04 attempt, verify actual session/container/bridge/baseline cleanup and publish a separate attributable acceptance report. INCONCLUSIVE is not product FAIL; uncertain restoration halts.

Actual read-only inspection uses SSH, public HTTP and Docker **image inspection**,
without starting Docker containers or browsers. Positive fresh observation fields
are not human authorization or acceptance evidence. Controlled launch/build
provenance is a reviewed trust boundary, not in-memory/kernel attestation. Existing
scheduler-off baseline, backup and automatic startup-scan disclosure remain intact.
Private baseline/inspection evidence is under the earlier preparation evidence
root's `pilot-runtime-proof/`; reserved case evidence/control/bridge paths remain
empty. Do not remove the shared lock/ledger, recreate an interrupted output path,
re-enable schedules, change assertions or bypass the launcher with manual argv.
