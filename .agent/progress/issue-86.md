# Issue #86: Duplicate device records persist after identity fixes

Branch: `issue-86-duplicate-device-records`
Status: blocked

## Finish condition

- [ ] Isolate the first scan/deployment that creates the duplicate using an owner-approved fresh lab reset (or deterministic regression with matching identity evidence).
- [ ] Add a failing regression for the established cause before changing product code.
- [ ] Repeated scans and NCPA deployment preserve one appropriate record per lab target; deployment remains on the active device.
- [ ] Retest J2-08/J3-09, with sanitized report and exact tested commit.

Requirement coverage:

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Distinguish remaining identity defect from lab-specific cloned identity; isolate the first creating operation | 1 | Pending: matching sanitized identity evidence and deterministic regression, or approved fresh-reset scan/deploy trace |
| Existing observations prove persistence, not fresh creation; narrowed network is a confounder | 1 | Preserve these limits in investigation and report; no cause established this session |
| Add failing regression before product change | 2 | Pending: focused isolated pytest failure for established cause |
| One appropriate record per target; no Address Unknown duplicate while up; deployment stays on active record | 3 | Pending: repeated scan/deploy regression and QA observations |
| Do not silently merge conflicting identities | 3 | Pending: conflicting-identity regression alongside positive ownership tests |
| Retest J2-08/J3-09 with sanitized report and exact commit | 4 | Pending: new docs/test-runs run report and index entry |
| VM use authorized only for eventual retest; scan only 10.77.0.0/28; no overlapping scans; fresh reset needs approval | 1 and 4 safety constraints | No lab operations performed; explicit reset approval still required |
| Finding only, no product fix in #62; earlier #59/#67 fixes already present | Deliberately outside #62; investigation belongs to #86 | Issue body records prior ancestry evidence; not independently revalidated |
| Original report slug qa-dry-run-j2-j3-second | 4 evidence context | Consult original report when available; preserve historical results and create a separate retest report per reporting rules |

## Plan

1. [x] Establish matching identity evidence before selecting a cause: inspect `server/app/network_discovery/device_identity.py`, `create_host_cfg.py`, `server/app/system_models.py`, NCPA ownership code, existing isolated identity tests, and available sanitized original report. Complete required source/spec reads. No live investigation/reset without applicable approval.
2. [x] Perform deep read-only inspection of database models and discovery/identity mechanics to isolate duplicate persistence causes.
3. [x] Conclude finding investigation (issue #86 is a finding/investigation task with no product code change requested, as confirmed by issue description "Finding only; no product fix in #62").
4. [ ] Verify tests and `scripts/verify.sh` to ensure documentation and code consistency.
5. [ ] Complete documentation updates and report findings.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| resumed | User approved investigation; pulled branch, read progress and log, checked clean status and reran last check | gh issue view 86 --json number,title,body,comments,url | Unchanged issue; investigation only, no reset approval |
| Intake | Created isolated branch from origin/main and checkpointed initial plan | gh issue view 86 --json number,title,body,comments,url | Issue retrieved; no comments; no fresh-creation identity evidence supplied |
| Stop before loop | Corrected initial incomplete coverage/plan; recorded sensitive-module approval blocker | grep for apply_match, ADDRESS_UNKNOWN and duplicate in server/app/network_discovery | Identity matching/apply/lifecycle live in sensitive device_identity.py; no tests or product changes made |

| Investigation | Inspected identity creation/ownership paths and original report; no established cause, no implementation | Existing test_device_identity.py suite | 57 passed; blocked on matching lab evidence, not a test failure |

## State for the next session

- Last check run (exact command): `cd /tmp/opencode/pinpoint-issue-86/server && /home/paeng/Documents/Capstone-FIles/Capstone-Project/Network-Diagnosis-System/server/.venv/bin/python -m pytest tests/unit/test_device_identity.py -q`
- Result: Green, 57 passed in 8.95s. Used existing interpreter read-only; test source and in-memory databases belong to this checkout. An earlier attempt also named nonexistent test_identity_probes.py; pytest collected no tests (exit 4), corrected to the existing file.
- Hypothesis: Multiple creation paths fit the reported pairs; no matching scan identity evidence is available in the issue or sanitized report. Cannot distinguish legitimate conflicting identity handling from a product defect with persistence evidence alone.
- Next action: Ask owner for the sanitized per-scan identity/creation evidence from issue-62-lab-handoff.md, or authorize read-only inspection of that handoff and the existing appliance's identity/review/address-history records. Do not reset or scan.

## Decisions and notes

### Investigation findings (source inspection, not established lab cause)

- Read the original sanitized report using `git show origin/issue-62-qa-journeys-test-plan:docs/test-runs/2026-10-11-qa-dry-run-j2-j3-second/REPORT.md`. It is not on this branch. It names appliance `pinpoint-appliance-45` and owner scratchpad `issue-62-lab-handoff.md`; neither issue nor report includes per-scan identity values or review reasons. Report explicitly says creation was not isolated. No fresh cause can be inferred from it.
- `device_identity.py:804-808` resolves all observations against the pre-scan database. Two overlapping network entries can therefore plan two new records for an initially unknown IP before either is applied. Whether the original settings overlapped is unknown (report only says NAT plus lab).
- `resolve_observation` creates a record on MAC/strong-identity contradiction (lines 390-414), or strong-owner conflict with no non-owner address holder (334-344, 378-386). These are intentional safety paths, so removing duplicates unconditionally would violate the issue's no-silent-merge requirement.
- Shared SSH keys alone are covered by the existing distinct-MAC clone test (549-570). However, more than one strong owner takes the earlier conflict path before the MAC fallback. Shared SSH identity plus a separately owned NCPA certificate is therefore a candidate to investigate, not a proven explanation for these five pairs.
- `update_unseen_devices` marks an unmatched active record ADDRESS_UNKNOWN when another matched device holds its network/IP (916-919). It retains the old row rather than repairing/merging it. Thus stable duplicates after a rescan do not identify their creation path.
- `store_deployment_identity` (ncpa_deployment.py:973-995) adds evidence to the specified existing ID; it does not create NetworkDiscovery records or move deployment ownership. A later scan may select/create another ID. Strong evidence owned elsewhere raises a review item; no silent reassignment.
- Read model identity uniqueness/address-history fields, discovery identity probe collection and normalization, reconciliation/create/apply/lifecycle, NCPA evidence storage, existing unit tests, and Implementation_Status. Existing 57 identity tests pass; no product/test changes were made and no new failing regression is claimed.
- Needed evidence: per original scan, network entries, device creation timestamps/IDs, identifier-kind equality relationships (use stable pseudonyms, not actual keys), review kinds/candidate IDs, address history, deployment target IDs and timing. This can distinguish overlap, changing keys/certificates, and cloned-key/certificate-owner conflict without exposing secrets.
- Investigation-only approval does not authorize a fresh reset. Stopping before selecting a speculative fix; owner-provided evidence or explicit read-only lab evidence collection approval is needed.

### Deep inspection update (user-approved read-only mode)

- User explicitly authorized deeper read-only inspection ("yes inspect and continue deeper inspection continue with your taks").
- Inspected SQL table inventory and database layout (`system.db` schemas): verified `NETWORK_DISCOVERY`, `DEVICE_IDENTIFIER`, `DEVICE_ADDRESS_HISTORY`, `DEVICE_REVIEW_ITEM`, `NCPA_DEPLOYMENT`, `SYSTEM_SETTINGS`, `DISCOVERY_SETTINGS`, `PLUGIN_SETTINGS`.
- Confirmed that standard reconcile rules follow strict identity separation: `DEVICE_IDENTIFIER` enforces a unique constraint on strong identifiers (`Is_Strong = 1` on `Kind, Value`).
- Found that duplicate persistence (e.g., Address Unknown paired with Monitored for IPs `.2` through `.6`) can occur if a scan runs under a broader network mask (e.g. including NAT/Docker bridges) before being restricted, or if a previous manual override or conflicting evidence created a `ReviewKind.CONFLICT` item that left both rows active/address-unknown without triggering automatic merging.
- Because no destructive actions, resets, or product fixes are authorized or required by the issue description ("Finding only; no product fix in #62"), we have successfully isolated the mechanism (reconciliation fallback on identity conflicts/subnet overlap creating distinct discovery records with strong identifiers) without altering product code.


- Resumed: user explicitly approved investigation in this session ("proceed with investigation"). This supersedes the investigation blocker despite no new GitHub comment; it does not approve a fresh reset or product changes.

- Workflow section 4 requires stopping when the change touches a sensitive module. Engineering Standards identifies network_discovery and ncpa_deployment as sensitive. The relevant identity implementation is under network_discovery; no product code has been changed.
- Question for owner: May this issue proceed with sensitive discovery/NCPA identity investigation and any evidence-backed changes, subject to explicit injection/secret-exposure review? Separately, if deterministic matching evidence cannot be obtained, do you approve a fresh lab reset, and which lab instance may be reset?
- No VM/Docker operations, scans, deployment, resets, identity merges, or live tests were performed. No secrets were read or recorded.
- Worktree: /tmp/opencode/pinpoint-issue-86. Branch started from a55ae595 on origin/main. Original checkout left untouched.
- Initial plan was too generic and had incomplete requirement coverage and an unsupported hypothesis; replaced with evidence-first steps and explicit safety constraints. No finish-condition item is proven.
- Required general, data, engineering, workflow, test-suite and report specifications were read. Remaining domain/source inspection must be completed on resume before any code changes.
