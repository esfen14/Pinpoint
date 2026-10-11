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

1. [ ] Establish matching identity evidence before selecting a cause: inspect `server/app/network_discovery/device_identity.py`, `create_host_cfg.py`, `server/app/system_models.py`, NCPA ownership code, existing isolated identity tests, and available sanitized original report. Complete required source/spec reads. No live investigation/reset without applicable approval.
2. [ ] Add a deterministic failing regression for the established cause in `server/tests/unit/`, recording its exact failure here. If evidence is insufficient, request owner-approved fresh-reset trace instead of inventing identity fixtures as proof.
3. [ ] After sensitive-module approval, make the smallest evidence-backed change in the owning identity/deployment source; preserve conflicting-identity review and add scan/deployment ownership coverage in `server/tests/unit/`. Run focused tests then `scripts/verify.sh backend`.
4. [ ] Retest J2-08/J3-09 under approved lab constraints; record exact tested commit and sanitized observations in a new `docs/test-runs/<date>-issue-86-retest/REPORT.md` and index in `docs/test-runs/README.md`.
5. [ ] Re-read issue and comments and prove each requirement. Update owning `spec files/Data_Model_and_Integrations.md` and `spec files/Implementation_Status.md` as applicable, run docs then all verification, remove this file only when complete, and open the template-based PR without merging.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| Intake | Created isolated branch from origin/main and checkpointed initial plan | gh issue view 86 --json number,title,body,comments,url | Issue retrieved; no comments; no fresh-creation identity evidence supplied |
| Stop before loop | Corrected initial incomplete coverage/plan; recorded sensitive-module approval blocker | grep for apply_match, ADDRESS_UNKNOWN and duplicate in server/app/network_discovery | Identity matching/apply/lifecycle live in sensitive device_identity.py; no tests or product changes made |

## State for the next session

- Last check run (exact command): `gh issue view 86 --json number,title,body,comments,url`
- Result: Issue retrieved successfully with empty comments. Plain `gh issue view 86` fails due to the installed CLI's deprecated projectCards GraphQL field; explicit JSON works.
- Hypothesis: Cause is unknown. Persistence evidence alone cannot establish cloned identities, scan identity loss, or deployment reassignment. Do not treat any of these as established.
- Next action: Obtain explicit approval to investigate/change sensitive discovery/NCPA identity code, with injection and secret-exposure review, before resuming the planned investigation.

## Decisions and notes

- Workflow section 4 requires stopping when the change touches a sensitive module. Engineering Standards identifies network_discovery and ncpa_deployment as sensitive. The relevant identity implementation is under network_discovery; no product code has been changed.
- Question for owner: May this issue proceed with sensitive discovery/NCPA identity investigation and any evidence-backed changes, subject to explicit injection/secret-exposure review? Separately, if deterministic matching evidence cannot be obtained, do you approve a fresh lab reset, and which lab instance may be reset?
- No VM/Docker operations, scans, deployment, resets, identity merges, or live tests were performed. No secrets were read or recorded.
- Worktree: /tmp/opencode/pinpoint-issue-86. Branch started from a55ae595 on origin/main. Original checkout left untouched.
- Initial plan was too generic and had incomplete requirement coverage and an unsupported hypothesis; replaced with evidence-first steps and explicit safety constraints. No finish-condition item is proven.
- Required general, data, engineering, workflow, test-suite and report specifications were read. Remaining domain/source inspection must be completed on resume before any code changes.
