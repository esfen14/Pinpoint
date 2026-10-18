# next-permissions — 2026-10-18

**PASS: two scripted browser cases, three expected items, verified restoration.**
This is one fixed permission batch, not whole Accounts/NCPA module acceptance.

Plan: [current black-box catalog](../../qa/Pinpoint%20-%20Black-Box%20Test%20Cases%20by%20Module%20with%20Traceability%20Matrix.md).
[Prepared scope](../../qa/Next_Permission_Batch_Review.md) ·
[queue JSON](../../qa/queues/2026-10-18-next-permissions.json) ·
[execution log](../../qa/queues/2026-10-18-next-permissions-execution.md).

## Provenance and authorization

| Field | Observed value |
|---|---|
| Tracking / responsible owner | [#206](https://github.com/esfen14/Pinpoint/issues/206) / Paeng |
| Queue / set / session | `2026-10-18-next-permissions.json` / `next-permissions` / `next-permissions` |
| Scope checksum | `ca29de08cd8210d184872b6f016eeb806d003bd686a23c4481d2d646fc4dedc5` |
| Catalog SHA-256 | `d9374c41d7f4e5304c3475735d765ad66cb4352cc9745f76e96d78c4de0e398f` |
| Fixed batch / order | `next-permissions-001`: TC-ACC-09, then TC-NCPA-08 |
| Actual application | `299ab3ba7203c89a3ca5d8fabea42d9e5f239be2`, independently matched to controlled launch/runtime and served files |
| Harness | `7947da1a686c2ad2a4d98dabc9f83c7baced3e34`; reporting/progress-only changes during execution |
| Controlled baseline | `da42da6cdbc38dab7ba6f9d96c2abd9cfb822123429fdd3f1e613ea50f8e07c3` |
| Environment | Exclusive local VirtualBox `pinpoint-qa-appliance`, UUID `351eb491-f5e1-4854-a7e4-68309ad774ad` |
| Executor | Scripted automation: pinned TypeScript Playwright 1.64.0/Chromium, isolated no-network containers and owned bridge; Codex orchestration/evidence review |
| Human contribution | Paeng approved exclusive ownership, exact handoff and start; no human performed a browser step |
| User approval | `2026-10-18T09:25:04.858226+00:00`; “approve the handoff and start the next-permissions” |
| Reviewed handoff proof | `2026-10-18T09:25:41.260526+00:00` |
| Batch opened / completed | `2026-10-18T09:27:09.405748+00:00` / `2026-10-18T09:27:32.939620+00:00` |
| Independent final audit | `2026-10-18T09:28:05.785006+00:00` |
| Installer | Existing appliance; no installer operation or new installer-version claim |
| Raw evidence | Private host directory `/home/paeng/pinpoint-test-results/2026-10-18-issue-206-next-permissions`; never committed |

Before launch, source-current queue/card checks passed and docs/frontend CI
succeeded at the exact harness commit. Separate private expiring grants were
created only after actual user approval. An initial reviewer-label semicolon was
rejected at grant preparation before probes/disposition/consumption; correcting
that metadata passed the same gate. No test/card/fixture/assertion or product code
changed, and no case was retried. Browser execution needed no intervention.

## Actual case results

| Case | Result | Coverage and restoration | Initial attempts |
|---|---|---|---|
| TC-ACC-09 | PASS | E1, E2 accepted; logout/resource/baseline cleanup verified | 1 |
| TC-NCPA-08 | PASS | E1 accepted; logout/resource/baseline cleanup verified | 1 |

| Expected item | Verdict | Observed value | Observation UTC | Private evidence reference |
|---|---|---|---|---|
| TC-ACC-09 E1 | PASS | Manage Accounts absent from sidebar; direct address redirects to Settings. | `2026-10-18T09:27:17.818Z` | `evidence/TC-ACC-09/observed-TC-ACC-09-E1.json` |
| TC-ACC-09 E2 | PASS | Accounts API address returns 403. | `2026-10-18T09:27:17.838Z` | `evidence/TC-ACC-09/observed-TC-ACC-09-E2.json` |
| TC-NCPA-08 E1 | PASS | NCPA Deployment absent from sidebar; direct address redirects to Settings. | `2026-10-18T09:27:29.543Z` | `evidence/TC-NCPA-08/observed-TC-NCPA-08-E1.json` |

Each adapter signed in through the real UI as the existing initialized Staff user,
checked Staff/zero permissions/completed setup, navigated the written page address,
and asserted the actual sidebar absence, Settings URL and visible Settings heading.
TC-ACC-09 then browser-navigated `/api/user/accounts` and observed HTTP 403.
No response interception, mock or shell action replaced a required UI interaction.
The parser independently validated every fixed item, selected case/project/config,
initial attempt and attach time bounds before acceptance.

Both adapters performed supported logout and observed `/api/user/me` 401;
independent browser contexts were disposed. Source configuration disables retries,
trace/video/screenshots and extra setup projects; each owned container selected
one exact ID. Per-case supervised envelope durations were 11.776907 and 11.748046
seconds respectively; these include verification/cleanup and are not application
performance measurements.

## Counts

- TC: selected 2, attempted 2, definitive PASS 2, FAIL 0, partial 0, blocked 0,
  inconclusive 0, Not run 0. Three of three expected items accepted.
- E2E: selected/attempted 0/0. Inherited full-case credit 0.
- One batch opened/completed (1/1); two initial attempts, zero diagnostic repeats.
- This set is complete and consumed. No later set was opened or authorized.

## Cleanup and preserved history

The supervisor accepted logout, owned container exit/removal/daemon absence,
bridge shutdown/socket removal, idle bounded process runners and fresh baseline
proof after each case. A separate final read-only audit then matched both accepted
results/item files/session/custody against the canonical ledger, queried actual
container absence by owned ID and name, checked processes and Unix endpoints,
and repeated actual host/guest/runtime/config/dependency/Staff/served-byte and
image/browser verification. Those checks passed with unchanged evidence and
baseline. See private `control/final-audit/final-proof.json` and retained query/probe
outputs. Session closure and every required resource absence are verified.

The canonical ledger now has four total attempts: the preserved original halted
TC-SS-04 attempt, its separately started accepted recheck, and these two complete
PASS attempts. Active halt is false. One original recovery disposition and one
new audited handoff remain; readiness validates their exact archives and history
prefixes. Original attempts, artifacts, recovery archive and session budgets were
not cleared, relocated or rewritten. Original human catalog results remain intact.

VM stays running with the existing scheduler-off override, accounts/configuration,
five devices and three scan records matching the baseline. Only attributable
login/logout audit side effects were expected; none were erased. No scan, fault,
account reset, NCPA deployment, scheduler change, restart or snapshot restore was
performed. No product defect was established and no finding/retry was needed.

## Next action and verification

This batch is complete; prepare the next finite module/case assignment separately.
One or two related modules per assignment can reduce preparation churn, but only
explicit source-mapped cases with ready fixtures may execute; the present launcher
still supports only its three literal permission IDs. Further modules need a
separate preparation/review rather than substituting or draining unlisted cases.
Broader unattended readiness and the remaining 232 unmapped definitions are open.

Final reporting-only `scripts/verify.sh docs` passed 200 isolated contracts;
source-current consumed-queue, document/progress and whitespace checks passed.
No unchanged frontend or local backend suite is required for this result-recording
pass. Final reporting-commit CI is separate from the successful pre-run CI.
