# Project Documents

Working documents that are **not** system specifications. The authoritative
description of what Pinpoint is and must do lives in
[`spec files/`](../spec%20files/README.md); read that first.

| Folder | What belongs here | Lifecycle |
|---|---|---|
| [`plans/`](plans) | Implementation plans, design proposals, acceptance and remediation reports tied to one piece of work | Starts as a draft with a **Status** line. When the work ships, fold what is still true into the matching spec, then delete the plan or mark it closed. Open defects belong in GitHub issues |
| [`archive/`](archive) | Finished plans and the 25 planned issues, kept for history and inbound links | Read-only record; not a specification. Each folder has a README saying what the files were for |
| [`manuals/`](manuals) | How-to guides for operators and users | Kept current with the feature |
| [`qa/`](qa/QA_Journeys_and_Scope.md) | Six documents: [scope](qa/QA_Journeys_and_Scope.md), [current black-box catalog](qa/Pinpoint%20-%20Black-Box%20Test%20Cases%20by%20Module%20with%20Traceability%20Matrix.md), [derived status](qa/QA_Case_Status.md), [module queues](qa/QA_Run_Queues.md), [Playwright setup](qa/Playwright_Setup.md) and [automation readiness](qa/Automation_Readiness.md) (with the generated [coverage view](qa/Automation_Coverage.md)), plus JSON data files whose generating scripts are listed in the readiness guide | Preserve human results; new executions go in immutable `test-runs/` reports. One-off reviews are filed in `test-runs/`, not here. Regenerate the derived view after source/evidence changes |
| [`reference/`](reference) | Third-party reference material kept for lookup, such as [`nagios-openapi.json`](reference/nagios-openapi.json), an OpenAPI description of the Nagios Core 4.5.11 JSON CGI endpoints (captured from a lab appliance) | Not maintained against the product; replace it when the Nagios version changes |
| [`test-runs/`](test-runs/README.md) | Sanitized reports of live-lab and acceptance runs: commit tested, per-case results, issues raised | Permanent record; never edited to change a result |
| [`../server/tests/plans/`](../server/tests/plans/README.md) | Test plans and live-lab plans | Stay beside the tests they drive |

## Rules

Prepare and share fixed module/person case lists with
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

Appliance storage and bounded Nagios-log viewing are explained in
[Storage and Nagios logs](manuals/Storage_and_Nagios_Logs.md).

Automatic recovery rules and what PinPoint may restart are explained in
[Automatic recovery](manuals/Automatic_Recovery.md).

A guide for every page of the web interface is indexed in
[Pinpoint guides](manuals/README.md).

Current-case automation preparation: [coverage matrix](qa/Automation_Coverage.md)
and [adapter/card guide](qa/Automation_Readiness.md). Source implementation and
runtime acceptance are recorded separately.
