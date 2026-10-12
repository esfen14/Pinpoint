# Project Documents

Working documents that are **not** system specifications. The authoritative
description of what Pinpoint is and must do lives in
[`spec files/`](../spec%20files/README.md); read that first.

| Folder | What belongs here | Lifecycle |
|---|---|---|
| [`plans/`](plans/) | Implementation plans, design proposals, acceptance and remediation reports tied to one piece of work | Starts as a draft with a **Status** line. When the work ships, fold what is still true into the matching spec, then delete the plan or mark it closed. Open defects belong in GitHub issues |
| [`manuals/`](manuals/) | How-to guides for operators and users | Kept current with the feature |
| [`qa/`](qa/QA_Journeys_and_Scope.md) | The QA journeys and scope list ([`QA_Journeys_and_Scope.md`](qa/QA_Journeys_and_Scope.md)), master test plan ([`QA_Test_Plan.md`](qa/QA_Test_Plan.md)), and paper-ready test-case/result tables ([`QA_Paper_Test_Case_Tables.md`](qa/QA_Paper_Test_Case_Tables.md)) | Kept current with the product: update the plan or traceability matrix, then regenerate the tables. Detailed immutable run results go in `test-runs/`; the QA table is a current derived status ledger |
| [`test-runs/`](test-runs/README.md) | Sanitized reports of live-lab and acceptance runs: commit tested, per-case results, issues raised | Permanent record; never edited to change a result |
| [`../server/tests/plans/`](../server/tests/plans/README.md) | Test plans and live-lab plans | Stay beside the tests they drive |

## Rules

Prepare and share fixed ISO-scoped case lists with
[`QA_Run_Queues.md`](qa/QA_Run_Queues.md) before starting QA. Saved queues are
planning snapshots; executed results remain in `test-runs/`.

- A document that says "Status: draft", lists decisions still to be made, or
  records one test run is a plan or report, not a specification.
- Specifications state current behavior and constraints. They do not hold
  history, schedules or task lists.
- Code comments may point at a plan for background, but behavior must be
  described in a specification, because plans get closed and removed.
- Test results are recorded in `test-runs/`, not in plans. Plans say what to
  test; reports say what happened.
- Every plan names the spec it feeds. `scripts/verify.sh docs` checks that
  relative links in this folder still resolve.
