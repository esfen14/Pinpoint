# Next permission batch: TC-ACC-09 and TC-NCPA-08

State: prepared for review; no handoff or new case start. Owner Paeng, tracking
[#206](https://github.com/esfen14/Pinpoint/issues/206), set/session `next-permissions`.
[Queue preview](queues/2026-10-18-next-permissions.md) ·
[immutable JSON](queues/2026-10-18-next-permissions.json) ·
[preparation report](../test-runs/2026-10-18-issue-206-next-permissions-preflight/REPORT.md).

## Fixed scope

| Order | Case | Human summary / detail | Required evidence |
|---|---|---|---|
| 1 | TC-ACC-09 — The accounts page needs permission | Not run / Not run | E1: Manage Accounts sidebar link absent and direct `/accounts` redirects to Settings; E2: browser navigation to `/api/user/accounts` returns 403 |
| 2 | TC-NCPA-08 — NCPA Deployment needs permission | Not run / Not run | E1: NCPA Deployment sidebar link absent and direct `/ncpa-deployment` redirects to Settings |

One ordinary batch `next-permissions-001`, two cases, one initial attempt each,
no diagnostic repeat, no automatic retry/resume or replacement IDs. TC-SS-04 is
excluded because its separately started #211 recheck already passed. Other human
PASS cases and all unlisted cases are excluded. TC and E2E counts stay separate.
The queue copies each full catalog procedure, expectations and prerequisite text.

## Actual environment and source review

- Target application `299ab3ba7203c89a3ca5d8fabea42d9e5f239be2`, exclusive local
  VirtualBox `pinpoint-qa-appliance`, UUID `351eb491-f5e1-4854-a7e4-68309ad774ad`.
- Supported read-only inspection passed at `2026-10-18T09:06:49.892257+00:00`. Controlled source,
  runtime/config/dependency/process/boot, Staff, served artifacts and image/browser
  pins still matched the previously reviewed baseline. It is a preparation
  observation; the handoff and each case acquire their own fresh checks.
- Existing initialized disposable Staff: Active user/role, zero permissions,
  setup complete, password change complete. Supported API login/logout is the only
  account side effect; login/logout audit entries remain attributable.
- Controlled scheduler-off baseline, five devices/three scan records preserved.
  This permission subset uses Staff denial behavior only: monitoring, incident,
  SMTP and deployed-NCPA data are not used as product evidence. No extra catalog
  case is executed to establish setup and no discovery/fault/NCPA operation occurs.
- Same fixed Playwright 1.64.0/Chromium pin, Docker network none, read-only source
  and root, owned Unix bridge to loopback appliance only, one worker and no capture.
- Accounts source reviewed: `pageAccess.ts`, `Sidebar.tsx`, guarded `/accounts`
  route and `available_accounts` with `account.view`; NCPA uses the literal
  `system.deploy.ncpa` page guard. Browser navigation follows the catalog steps;
  no mocked response or substituted API action supplies a required UI observation.
- Seven adapters have source coverage; 232 definitions remain unmapped. Source
  implementation and isolated fixtures do not establish a runtime PASS.

## Execution and cleanup contract

Only `python3 -I scripts/qa_pilot.py run` with the saved queue, set `next-permissions`,
owner Paeng, session `next-permissions` and matching private explicit start can
launch these cases. Cards contain the exact launcher/action vectors and selected
spec/project/title. The legacy runner and printed Docker argv must never be used
as a bypass. `PINPOINT_QA_CASES` is one exact ID per owned container.

Each case has a 300-second overall envelope, bounded 10-second browser actions,
15-second navigation, 60-second Playwright attempt, 90-second report envelope and
30-second cleanup/proof budget. Each receives separate evidence, control/container
and bridge directories beneath `/home/paeng/pinpoint-test-results/2026-10-18-issue-206-next-permissions`. The shared session journal is written
under `control/session.json`; every accepted result is saved before opening the
next fixed case. Persisted attempts and batch budgets cannot reset on restart.

The adapter performs supported logout and observes `/api/user/me` 401. The owned
container must exit/be removed with proved absence, the owned bridge must stop
and remove its socket, runners must be idle, and fresh baseline verification must
pass. Any missing item prevents PASS. A non-PASS stops the remaining assignment;
uncertain cleanup/interruption halts the ledger. Preserve raw private evidence;
no product repair, timeout/selector change, account reset, scheduler change, scan,
fault, snapshot restore, restart or alternative browser is authorized.

## Separate reviewed forward handoff

The previous [#211 v2 queue](queues/2026-10-18-issue-211-ss04-recheck-v2.json) is
complete and consumed; its source hashes are historical, not a launchable scope.
Local read-only audit verified its accepted observation files, terminal custody,
saved session and canonical history: two attempts, one recovery disposition,
original halt preserved, active halt false. No ledger state was changed.

Before any new attempt, separately approve `qa_pilot.py handoff` for this exact new
queue. Its expiring private review binds the current ledger checksum, frozen prior
queue/set/owner, accepted evidence digest, new queue/set/owner, UUID and unchanged
target/baseline. It independently verifies actual old container ID/name absence,
process/socket absence and fresh baseline. It archives exact old ledger bytes and
appends one forward assignment; all attempts, archives, recoveries and budgets
stay intact. Missing/changed proof or an unfinished prior queue rejects. It does
not start a case. A different next scope needs a new review; no store relocation.

Private `handoff-grant.json` and `start.json` are false templates. Preparation,
this review document and elapsed time cannot make them affirmative. Only after
Paeng explicitly approves the named handoff and starts this fixed set may the
preparing agent create matching short-lived affirmative records. A model executing
the set follows its cards and cannot invent these attestations or change scope.

## Reporting and stop point

Current selected: 2 TC, 0 E2E. Attempted: 0. New PASS/FAIL/partial/inconclusive: 0.
Not run: 2. Batches opened: 0. Handoff applied: no.
Use a new attributable run report and append the result to the queue execution log
and progress after execution; preserve the human catalog and earlier reports.
After both cases, stop this set. Broader and unattended readiness remains pending.
