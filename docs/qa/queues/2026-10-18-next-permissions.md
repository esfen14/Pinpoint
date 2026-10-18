# Prepared module QA queue

Waiting for explicit start. No tests have started.
Target revision: `299ab3ba7203c89a3ca5d8fabea42d9e5f239be2`; scope: `ca29de08cd8210d184872b6f016eeb806d003bd686a23c4481d2d646fc4dedc5`

## next-permissions — Paeng

Modules: ACC, NCPA; purpose: untested.
Five batches per session; at most five ordinary IDs per batch.

| Batch | Exact IDs |
|---|---|
| next-permissions-001 | TC-ACC-09, TC-NCPA-08 |

### Exclusions


### Card: TC-ACC-09 — The accounts page needs permission

Historical summary: Not run; detail: Not run.
Phase: 2; singleton: False; requirements: REQ-ACC-08
Source adapter coverage: implemented / scripted automation (not a runtime result).

Module setup/notes:
### Module 2 – Manage Accounts (`/accounts`)

**Summary of cases**

| TC | Case | Req | Tech | Pri | Result |
| --- | --- | --- | --- | --- | --- |
| TC-ACC-01 | Add an account | ACC-01 | EP | H | PASS |
| TC-ACC-02 | Duplicate and invalid emails are refused | ACC-01 | EP | M | PASS |
| TC-ACC-03 | "Require password change at first sign-in" | ACC-02 | EG | M | PASS |
| TC-ACC-04 | Inactive and suspended users cannot sign in | ACC-03 | DT | H | PASS |
| TC-ACC-05 | Editing a signed-in user signs them out | ACC-04 | ST | M | FAIL |
| TC-ACC-06 | Administrator resets another user's password | ACC-05 | ST | H | FAIL |
| TC-ACC-07 | The first (bootstrap) account is protected | ACC-06 | DT | H | PASS |
| TC-ACC-08 | "Send this user email alerts" depends on permission | ACC-07 | DT | L | Not run |
| TC-ACC-09 | The accounts page needs permission | ACC-08 | DT | H | Not run |
| TC-ACC-10 | Add User uses the default role (issue #191) | ACC-09 | EG | M | Not run |



Prerequisites:
| TC-ACC-04, 05, 07, 09, 10 | TC-ACC-01 | They need the Staff user |

#### TC-ACC-09 – The accounts page needs permission

**Requirement:** REQ-ACC-08 · **Technique:** DT · **Priority:** H · **Result:** Not run

**Steps**

1. Sign in as the Staff user.
2. Type `/accounts` in the address bar.
3. Open `/api/user/accounts` in the address bar.

**Expected result**

- **Manage Accounts** is not in the sidebar, and `/accounts` redirects to Settings.
- The API returns 403.

Expected-item evidence checklist:

- E1: **Manage Accounts** is not in the sidebar, and `/accounts` redirects to Settings.
- E2: The API returns 403.

Execution adapter/card (empty means BLOCKED):
```json
{
  "readiness": "Source-reviewed fixed intent; awaiting exact reviewed handoff and explicit new set start; no authorization from preparation.",
  "coverage_hash": "507026187f44dc0e588b0b114c124f2b4c408860f7197c686cff8d8df8a20d1f",
  "selection": {
    "path": "client/e2e/qa-permissions.lab.spec.ts",
    "title": "TC-ACC-09: The accounts page needs permission",
    "project": "qa-permissions",
    "config": "client/playwright.qa.config.ts"
  },
  "mode": "scripted automation",
  "adapter": "/home/paeng/Documents/Capstone-FIles/Capstone-Project/Network-Diagnosis-System-qa-readiness/client/e2e/qa-permissions.lab.spec.ts",
  "adapter_hash": "a6edb79e3d7edb4c040e149f927ad242cc34d4f6eb615af4f8a5bdcaeb8d6ddf",
  "actions": [
    [
      "scripts/playwright-lab",
      "--config=playwright.qa.config.ts",
      "--project=qa-permissions",
      "e2e/qa-permissions.lab.spec.ts",
      "--grep=(?:^| )TC\\-ACC\\-09:\\ The\\ accounts\\ page\\ needs\\ permission$",
      "--workers=1",
      "--retries=0"
    ]
  ],
  "reviewed_by": "Codex source/spec/assertion/cleanup review, 2026-10-18; supported actual read-only baseline inspection at 2026-10-18T09:06:49.892257+00:00; no case start.",
  "timeout_seconds": 300,
  "step_timeout_seconds": 30,
  "human_required": false,
  "prerequisites": [
    "Exclusive local pinpoint-qa-appliance UUID 351eb491-f5e1-4854-a7e4-68309ad774ad owned by Paeng, as explicitly confirmed; fresh host/controller/endpoint proof is rechecked before each operation.",
    "Exact controlled target 299ab3ba7203c89a3ca5d8fabea42d9e5f239be2 and baseline da42da6cdbc38dab7ba6f9d96c2abd9cfb822123429fdd3f1e613ea50f8e07c3; source/runtime/config/dependencies/processes/boot/served artifacts match supported read-only inspection; recheck freshly at handoff and every case.",
    "Existing initialized disposable Staff Active, role Active, zero permissions, needs_setup=false and must_change_password=false; private credential identity pinned. No account creation/reset or other catalog prerequisite case is run.",
    "Scheduler remains off, five devices and three scan records preserved. These permission cases do not use monitoring/incident/SMTP/deployed-NCPA data as evidence; no new scan, fault, restart, scheduler or fixture change is in scope.",
    "Matching pinned local container image and cached Playwright 1.64.0 Chromium headless-shell revision 1248/binary; no download/install during run.",
    "Canonical ledger remains after complete #211 v2: original halted attempt/archive plus accepted PASS preserved. Before new consumption use only separately reviewed handoff with exact source checksum/evidence/next queue hash, fresh terminal-resource absence and baseline proof.",
    "Only after explicit approval of this handoff and start of next-permissions for Paeng may matching expiring affirmative handoff/start records be written. Existing private records are false templates, not approval.",
    "All case evidence/control/bridge paths must be same-owner, private, canonical, disjoint and initially empty. Serial execution only; save each result before the next case. Stop on any non-PASS or uncertainty."
  ],
  "recovery": [
    "Supported logout and /api/user/me 401 must be attached; independent browser contexts are disposed. Login/logout audit entries remain attributable.",
    "Owned container removal/actual absence, bridge stop/socket absence, idle bounded process runners and fresh unchanged baseline are mandatory before accepting restoration.",
    "No diagnostic repeat or automatic resume. On non-PASS stop remaining scope. On interruption/cleanup uncertainty preserve halted ledger and raw evidence for separately reviewed recovery; never delete/relocate locks/store, reuse outputs or repair the application."
  ],
  "evidence_dir": "/home/paeng/pinpoint-test-results/2026-10-18-issue-206-next-permissions/evidence/TC-ACC-09",
  "write_paths": [
    "/home/paeng/pinpoint-test-results/2026-10-18-issue-206-next-permissions/evidence/TC-ACC-09",
    "/home/paeng/pinpoint-test-results/2026-10-18-issue-206-next-permissions/control",
    "/home/paeng/pinpoint-test-results/2026-10-18-issue-206-next-permissions/bridge",
    "/home/paeng/pinpoint-test-results/2026-10-18-issue-206-next-permissions/handoff"
  ],
  "container_image_id": "sha256:e37b02e1817b35e6a0953bdfed1e4a285cc9f3d1d86ac77c1d2fedef0da6c7a5",
  "control_dir": "/home/paeng/pinpoint-test-results/2026-10-18-issue-206-next-permissions/control/TC-ACC-09",
  "bridge_dir": "/home/paeng/pinpoint-test-results/2026-10-18-issue-206-next-permissions/bridge/TC-ACC-09",
  "journal_path": "/home/paeng/pinpoint-test-results/2026-10-18-issue-206-next-permissions/control/session.json",
  "public_write_paths": [
    "docs/test-runs/2026-10-18-next-permissions/REPORT.md",
    "docs/test-runs/README.md",
    "docs/qa/queues/2026-10-18-next-permissions-execution.md",
    ".agent/progress/issue-206.md",
    ".agent/progress/ai-testing-readiness.md",
    ".agent/progress/ai-testing-today.md"
  ],
  "baseline_hash": "da42da6cdbc38dab7ba6f9d96c2abd9cfb822123429fdd3f1e613ea50f8e07c3",
  "launcher_argv": [
    "python3",
    "-I",
    "scripts/qa_pilot.py",
    "run",
    "--queue",
    "docs/qa/queues/2026-10-18-next-permissions.json",
    "--run",
    "next-permissions",
    "--owner",
    "Paeng",
    "--session",
    "next-permissions",
    "--grant",
    "/home/paeng/pinpoint-test-results/2026-10-18-issue-206-next-permissions/start.json",
    "--baseline",
    "/home/paeng/pinpoint-test-results/2026-10-18-issue-206-preparation/pilot-runtime-proof/baseline.json",
    "--state-dir",
    "/home/paeng/.local/share/pinpoint-vmlab-45",
    "--bridge-dir",
    "/home/paeng/pinpoint-test-results/2026-10-18-issue-206-next-permissions/bridge",
    "--control-dir",
    "/home/paeng/pinpoint-test-results/2026-10-18-issue-206-next-permissions/control"
  ],
  "handoff_argv": [
    "python3",
    "-I",
    "scripts/qa_pilot.py",
    "handoff",
    "--queue",
    "docs/qa/queues/2026-10-18-next-permissions.json",
    "--prior-queue",
    "docs/qa/queues/2026-10-18-issue-211-ss04-recheck-v2.json",
    "--grant",
    "/home/paeng/pinpoint-test-results/2026-10-18-issue-206-next-permissions/handoff-grant.json",
    "--baseline",
    "/home/paeng/pinpoint-test-results/2026-10-18-issue-206-preparation/pilot-runtime-proof/baseline.json",
    "--control-dir",
    "/home/paeng/pinpoint-test-results/2026-10-18-issue-206-next-permissions/handoff"
  ],
  "tracking_issue": 206,
  "review_document": "docs/qa/Next_Permission_Batch_Review.md",
  "prior_report": "docs/test-runs/2026-10-18-issue-211-ss04-recheck/REPORT.md"
}
```

### Card: TC-NCPA-08 — NCPA Deployment needs permission

Historical summary: Not run; detail: Not run.
Phase: 3; singleton: False; requirements: REQ-NCPA-06
Source adapter coverage: implemented / scripted automation (not a runtime result).

Module setup/notes:
### Module 12 – NCPA Deployment (`/ncpa-deployment`)

**Summary of cases**

| TC | Case | Req | Tech | Pri | Result |
| --- | --- | --- | --- | --- | --- |
| TC-NCPA-01 | Warning when `check_ncpa` is off | NCPA-01 | EG | M | Not run |
| TC-NCPA-02 | Deploy wizard order | NCPA-02 | ST | H | Not run |
| TC-NCPA-03 | Wrong and right SSH password | NCPA-02 | EP | H | Not run |
| TC-NCPA-04 | Run progress and history | NCPA-03 | ST | H | Not run |
| TC-NCPA-05 | Who can use Clean up | NCPA-04 | DT | M | Not run |
| TC-NCPA-06 | Clean up | NCPA-04 | EP | H | Not run |
| TC-NCPA-07 | No credentials shown anywhere | NCPA-05 | EG | H | Not run |
| TC-NCPA-08 | NCPA Deployment needs permission | NCPA-06 | DT | H | Not run |
| TC-NCPA-09 | Remote restart settings (issue #182) | NCPA-07 | EP | M | Not run |
| TC-NCPA-10 | Remote restart is blocked during a deployment | NCPA-07 | EG | M | Not run |
| TC-NCPA-11 | Clean up warns that remote restarts stop | NCPA-08 | EG | M | Not run |

The page has the **Devices** tab (a table with **Select**, **Device**, **IP Address**, **Agent**, **Host Key**, **Last Result**, **Actions**) and a **Deployment History** tab. Buttons: **Deploy selected**, **Verify**, **Clean up**, **Remote restart**.



Prerequisites:
| TC-ROL-05, TC-DASH-08, TC-SS-04, TC-HIS-01, TC-PLG-07, TC-NCPA-08, TC-RPT-07, TC-LOG-05, TC-MNT-09 | TC-ACC-01 | They use the Staff user |

#### TC-NCPA-08 – NCPA Deployment needs permission

**Requirement:** REQ-NCPA-06 · **Technique:** DT · **Priority:** H · **Result:** Not run

**Steps**

1. Sign in as the Staff user.
2. Type `/ncpa-deployment` in the address bar.

**Expected result**

- The page is not in the sidebar and the address redirects to Settings.

Expected-item evidence checklist:

- E1: The page is not in the sidebar and the address redirects to Settings.

Execution adapter/card (empty means BLOCKED):
```json
{
  "readiness": "Source-reviewed fixed intent; awaiting exact reviewed handoff and explicit new set start; no authorization from preparation.",
  "coverage_hash": "36899427a5c39cb8298efbd97221928c7dc70790cf7c1696df6059c53e6a3464",
  "selection": {
    "path": "client/e2e/qa-permissions.lab.spec.ts",
    "title": "TC-NCPA-08: NCPA Deployment needs permission",
    "project": "qa-permissions",
    "config": "client/playwright.qa.config.ts"
  },
  "mode": "scripted automation",
  "adapter": "/home/paeng/Documents/Capstone-FIles/Capstone-Project/Network-Diagnosis-System-qa-readiness/client/e2e/qa-permissions.lab.spec.ts",
  "adapter_hash": "a6edb79e3d7edb4c040e149f927ad242cc34d4f6eb615af4f8a5bdcaeb8d6ddf",
  "actions": [
    [
      "scripts/playwright-lab",
      "--config=playwright.qa.config.ts",
      "--project=qa-permissions",
      "e2e/qa-permissions.lab.spec.ts",
      "--grep=(?:^| )TC\\-NCPA\\-08:\\ NCPA\\ Deployment\\ needs\\ permission$",
      "--workers=1",
      "--retries=0"
    ]
  ],
  "reviewed_by": "Codex source/spec/assertion/cleanup review, 2026-10-18; supported actual read-only baseline inspection at 2026-10-18T09:06:49.892257+00:00; no case start.",
  "timeout_seconds": 300,
  "step_timeout_seconds": 30,
  "human_required": false,
  "prerequisites": [
    "Exclusive local pinpoint-qa-appliance UUID 351eb491-f5e1-4854-a7e4-68309ad774ad owned by Paeng, as explicitly confirmed; fresh host/controller/endpoint proof is rechecked before each operation.",
    "Exact controlled target 299ab3ba7203c89a3ca5d8fabea42d9e5f239be2 and baseline da42da6cdbc38dab7ba6f9d96c2abd9cfb822123429fdd3f1e613ea50f8e07c3; source/runtime/config/dependencies/processes/boot/served artifacts match supported read-only inspection; recheck freshly at handoff and every case.",
    "Existing initialized disposable Staff Active, role Active, zero permissions, needs_setup=false and must_change_password=false; private credential identity pinned. No account creation/reset or other catalog prerequisite case is run.",
    "Scheduler remains off, five devices and three scan records preserved. These permission cases do not use monitoring/incident/SMTP/deployed-NCPA data as evidence; no new scan, fault, restart, scheduler or fixture change is in scope.",
    "Matching pinned local container image and cached Playwright 1.64.0 Chromium headless-shell revision 1248/binary; no download/install during run.",
    "Canonical ledger remains after complete #211 v2: original halted attempt/archive plus accepted PASS preserved. Before new consumption use only separately reviewed handoff with exact source checksum/evidence/next queue hash, fresh terminal-resource absence and baseline proof.",
    "Only after explicit approval of this handoff and start of next-permissions for Paeng may matching expiring affirmative handoff/start records be written. Existing private records are false templates, not approval.",
    "All case evidence/control/bridge paths must be same-owner, private, canonical, disjoint and initially empty. Serial execution only; save each result before the next case. Stop on any non-PASS or uncertainty."
  ],
  "recovery": [
    "Supported logout and /api/user/me 401 must be attached; independent browser contexts are disposed. Login/logout audit entries remain attributable.",
    "Owned container removal/actual absence, bridge stop/socket absence, idle bounded process runners and fresh unchanged baseline are mandatory before accepting restoration.",
    "No diagnostic repeat or automatic resume. On non-PASS stop remaining scope. On interruption/cleanup uncertainty preserve halted ledger and raw evidence for separately reviewed recovery; never delete/relocate locks/store, reuse outputs or repair the application."
  ],
  "evidence_dir": "/home/paeng/pinpoint-test-results/2026-10-18-issue-206-next-permissions/evidence/TC-NCPA-08",
  "write_paths": [
    "/home/paeng/pinpoint-test-results/2026-10-18-issue-206-next-permissions/evidence/TC-NCPA-08",
    "/home/paeng/pinpoint-test-results/2026-10-18-issue-206-next-permissions/control",
    "/home/paeng/pinpoint-test-results/2026-10-18-issue-206-next-permissions/bridge",
    "/home/paeng/pinpoint-test-results/2026-10-18-issue-206-next-permissions/handoff"
  ],
  "container_image_id": "sha256:e37b02e1817b35e6a0953bdfed1e4a285cc9f3d1d86ac77c1d2fedef0da6c7a5",
  "control_dir": "/home/paeng/pinpoint-test-results/2026-10-18-issue-206-next-permissions/control/TC-NCPA-08",
  "bridge_dir": "/home/paeng/pinpoint-test-results/2026-10-18-issue-206-next-permissions/bridge/TC-NCPA-08",
  "journal_path": "/home/paeng/pinpoint-test-results/2026-10-18-issue-206-next-permissions/control/session.json",
  "public_write_paths": [
    "docs/test-runs/2026-10-18-next-permissions/REPORT.md",
    "docs/test-runs/README.md",
    "docs/qa/queues/2026-10-18-next-permissions-execution.md",
    ".agent/progress/issue-206.md",
    ".agent/progress/ai-testing-readiness.md",
    ".agent/progress/ai-testing-today.md"
  ],
  "baseline_hash": "da42da6cdbc38dab7ba6f9d96c2abd9cfb822123429fdd3f1e613ea50f8e07c3",
  "launcher_argv": [
    "python3",
    "-I",
    "scripts/qa_pilot.py",
    "run",
    "--queue",
    "docs/qa/queues/2026-10-18-next-permissions.json",
    "--run",
    "next-permissions",
    "--owner",
    "Paeng",
    "--session",
    "next-permissions",
    "--grant",
    "/home/paeng/pinpoint-test-results/2026-10-18-issue-206-next-permissions/start.json",
    "--baseline",
    "/home/paeng/pinpoint-test-results/2026-10-18-issue-206-preparation/pilot-runtime-proof/baseline.json",
    "--state-dir",
    "/home/paeng/.local/share/pinpoint-vmlab-45",
    "--bridge-dir",
    "/home/paeng/pinpoint-test-results/2026-10-18-issue-206-next-permissions/bridge",
    "--control-dir",
    "/home/paeng/pinpoint-test-results/2026-10-18-issue-206-next-permissions/control"
  ],
  "handoff_argv": [
    "python3",
    "-I",
    "scripts/qa_pilot.py",
    "handoff",
    "--queue",
    "docs/qa/queues/2026-10-18-next-permissions.json",
    "--prior-queue",
    "docs/qa/queues/2026-10-18-issue-211-ss04-recheck-v2.json",
    "--grant",
    "/home/paeng/pinpoint-test-results/2026-10-18-issue-206-next-permissions/handoff-grant.json",
    "--baseline",
    "/home/paeng/pinpoint-test-results/2026-10-18-issue-206-preparation/pilot-runtime-proof/baseline.json",
    "--control-dir",
    "/home/paeng/pinpoint-test-results/2026-10-18-issue-206-next-permissions/handoff"
  ],
  "tracking_issue": 206,
  "review_document": "docs/qa/Next_Permission_Batch_Review.md",
  "prior_report": "docs/test-runs/2026-10-18-issue-211-ss04-recheck/REPORT.md"
}
```

### Global setup and dependency source snapshot

# Pinpoint - Black-Box Test Cases by Module with Traceability Matrix

Oct 16, 2026 · @Raf

## Scope and approach

This suite tests Pinpoint module by module, the way a user (or an API client) sees it, with no knowledge of the code. Every test case tells you what to prepare, the exact steps to follow, and what you should see. Every case traces to a requirement taken from the repository's `spec files/` (see the traceability matrix at the end). It covers 23 modules plus 8 end-to-end scenarios, and it was checked against the repository's `main` branch at commit `4b1ad9f` (merged 2026-10-17).

**Black-box techniques used**

- **EP**: equivalence partitioning, one valid and one invalid class per input
- **BVA**: boundary value analysis, on limits the spec states (for example flap thresholds 0 to 100, retry interval 1 to 10 minutes)
- **DT**: decision table, for permission and state combinations
- **ST**: state transition, for pause/resume, acknowledge/unacknowledge, and enable/disable flows
- **EG**: error guessing, for empty states, cancelled dialogs, and double submits

**Conventions**

- **Test case ID:** `TC-<MODULE>-<nn>`, such as `TC-AUTH-03`.
- **Requirement ID:** `REQ-<MODULE>-<nn>`. The specs have no requirement IDs of their own, so each one here is a short statement of a spec rule and names its source section in the traceability matrix.
- **Priority:** H = a failure blocks the module or is a security issue, M = a failure breaks a feature, L = a cosmetic or edge case.
- **Result values:** PASS, FAIL (write what you saw), PARTIALLY PASS (write what was missing), BLOCKED (write which case blocked it), or Not run. Results already recorded by the tester are kept in this revision.
- **Passwords for test accounts:** use a value such as `Lab-Pinpoint-2026!`. It has 12 or more characters with upper and lower case letters, a number, and a symbol, so it passes both the strong policy (Settings, Security) and the relaxed policy (8 or more characters).
- **Data setup:** unless a case says otherwise, the lab has at least one host Up, one host Down, one service Critical, and one acknowledged alert.

The repository's `docs/qa/QA_Test_Plan.md` is organized by user journey (J1 to J9). This document regroups coverage by module and adds boundary, negative, and permission cases. Where a journey case covers the same check, the traceability matrix names it in the Source column (for example QA J1-03).

**How to read a test case**

- The first line gives the requirement, the technique, the priority, and the result.
- **Before you start** lists what must be ready. Skip it only if the case does not have one.
- **Steps** are done in order. Button, tab, and field names are in **bold** exactly as they appear on screen. Addresses and API paths are in `code`.
- **Expected result** is a list. Every item must be true for PASS.
- **Note** appears where the spec and the real app differ. The app's behavior is what you test, and the difference is reported as a finding.

**Test accounts and lab**

- **Super Admin:** the built-in role with every permission. It was called "Administrator" before issue #112. `flask sync-permissions` renames an existing one. If a different role already used the name "Super Admin", the old one is kept as "Administrator (Legacy)". On a development database filled by `flask seed`, the account is `admin@test.com` with password `Password123!` (development only).
- **Staff user:** any user whose role is the built-in **Staff** role. Staff holds no permissions, so after signing in the user can open only **Settings**, and only the **General Settings** tab. This one account is used wherever a case needs a user who is denied everything. On a development database use `emily.davis@test.com` with `Password123!`. On any other install create one in TC-ACC-01.
- **Dashboard-only user:** only a few cases need a user who can open the Dashboard and nothing else. Create the role `qa-view` with only `system.dashboard` (TC-ROL-01) and a user with that role.
- **Lab:** the Pinpoint appliance, a web VM (HTTP on port 80, SSH on port 22), a second Linux VM, an SMTP test mailbox, and a browser plus a private window for second sessions.

**Where to find each page**

| Sidebar label | Address | Permission needed |
| --- | --- | --- |
| Overview | `/dashboard` | `system.dashboard` |
| Network Health | `/network-health` | `system.network_health` |
| Device Inventory | `/device-inventory` | `system.network_health` |
| Topology | `/topology` | `system.network_health` |
| System Status | `/system-status` | `system.network_health` |
| Plugins | `/plugins` | `plugin.view` |
| NCPA Deployment | `/ncpa-deployment` | `system.deploy.ncpa` |
| Maintenance | `/maintenance` | `maintenance.manage` |
| Remediation | `/remediation` | `remediation.view` |
| History | `/history` | `system.history` |
| Report | `/reports` | `system.report` |
| System Logs | `/system-logs` | `system.logs` |
| Manage Accounts | `/accounts` | `account.view` |
| Manage Roles | `/manage-roles` | `role.view` |
| Settings | `/settings` | none. Tabs: General Settings (everyone), Security (`settings.security`), System (`settings.system`), Network Discovery (`settings.discovery`), Plugins (`settings.plugins`), Email (`settings.email`) |

A user who opens a page they may not use is sent to the first page they can use (a Staff user lands on Settings).

**What changed in this revision**

- **Role name:** "Administrator" is now "Super Admin" (#112).
- **Test users:** the old `viewer` and `noperm` are replaced by the Staff user, and a dashboard-only user only where a case needs one.
- **Steps:** every case now has numbered steps using the button and tab names in the app code.
- **Spec and app differ (marked Note in the case):** the Dashboard has four cards (Total Hosts, Network Latency, Active Warnings, Critical Issues), not the spec's Active Alerts and Hosts in Downtime cards. Unacknowledge asks no confirmation. The Active Alerts list has no acknowledgement filter. Rescan Network starts at once with no confirmation. The host table and host drawer are on Device Inventory, not Network Health.
- **New in `main` since the first revision:** resource forecast "Running out soon" (#156), remote service restart (#182), remediation safety controls and the kill switch (#155), the Add User default role fix (#191), and Clean up now offered on deployed devices.

## Run order and prerequisites

Some cases need something an earlier case creates, for example a user, a role, an active alert, or a deployed agent. Run the cases in the order below. Each case appears once, and the numbers continue within the same module ("TC-ACC-01, 02, 03" means TC-ACC-01, TC-ACC-02, TC-ACC-03). Run the 8 end-to-end scenarios afterwards on a freshly built (or restored) appliance.

### Run order

| Phase | Goal | Run these cases in this order |
| --- | --- | --- |
| 1 | Fresh install and first login (clean appliance) | TC-AUTH-05, 06, 07, 01, 02, 03, 04, 09, 12 |
| 2 | Roles and accounts (this creates the test users used later) | TC-ROL-01, 02, 03, TC-ACC-01, 02, 03, TC-AUTH-08, TC-ACC-04, 05, 06, 07, 09, 10, 08, TC-ROL-04, 05, 06, TC-AUTH-10, 11, TC-SHL-09, 04, 10 |
| 3 | Permission checks with the Staff user | TC-DASH-08, TC-SS-04, TC-HIS-01, TC-PLG-07, TC-NCPA-08, TC-RPT-07, TC-LOG-05, TC-SHL-06, TC-NFR-01, 02 |
| 4 | Settings the lab needs (email first) | TC-SET-07, 01, 02, 03, 04, 05, 06, TC-SHL-01, 02, 03 |
| 5 | Discover the network and enable plugins | TC-DSC-01, 02, 03, 04, 05, 08, 09, TC-PLG-01, 02, 03, 04, 05, 06, TC-DI-01, 02, 03, 04 |
| 6 | Views with live data, device extras, topology | TC-DASH-01, 05, 07, TC-NH-01, 02, 03, 04, 05, TC-SS-01, 02, 03, TC-DX-01, 02, 03, 04, 05, 06, 07, 08, 09, 10, TC-NH-06, 07, TC-TOP-01, 02, 03, 04, 05, 06 |
| 7 | Device changes | TC-DI-05, 06, 07, 08, 09, 11, 12, 13, TC-DASH-02, TC-DI-14, 15, 16, 17, 18, 19, TC-DSC-06, 07 |
| 8 | Faults, alerts, history, and maintenance | TC-DASH-03, TC-ACK-01, 02, 03, 04, 05, 06, 07, 08, TC-DASH-04, TC-HIS-02, 03, 04, 05, 06, 07, 08, TC-SHL-07, 08, TC-MNT-01, 02, 03, 04, 05, 06, 07, 09, 10 |
| 9 | NCPA and automatic recovery | TC-NCPA-01, 02, 03, 04, 05, 06, 07, 09, 10, 11, TC-DI-10, TC-DASH-09, TC-SS-05, TC-REM-02, 01, 04, 03, 05, 07, 09, 06, 08, 10 |
| 10 | Reports and logs (after incidents exist) | TC-RPT-01, 02, 03, 04, 05, 06, TC-LOG-01, 02, 03, 04, TC-SHL-05 |
| 11 | Cases that stop or break services (last, then restore everything) | TC-DASH-06, TC-MNT-08, TC-SET-08, 09 |
| 12 | Quality and performance | TC-NFR-03, 04, 05, 06, 07, 08, 09, 10, 11 |
| 13 | Edge cases | TC-EDG-01 to 18 |
| 14 | Order of events (one at a time, restore the lab after each) | TC-SEQ-01, 02, 03, 04, 05, 06, 07, 08, 10, 11, 12, 13, 14, 15, 16, 18, 19, 20, 21, 22, 23, 24 |
| 15 | Cases that need a fresh appliance (restore the clean snapshot before each one) | TC-SEQ-09, TC-SEQ-17, then E2E-01 to 08 |

### What each case needs first

Cases not listed here need only a finished setup (TC-AUTH-07) and the lab described above.

| Case | Do these first | Why |
| --- | --- | --- |
| TC-AUTH-06 | TC-AUTH-05 | The setup window must already be open |
| TC-AUTH-07 | TC-AUTH-06 | It uses the same window, now with correct values |
| TC-AUTH-01 to 04, 09, 12 | TC-AUTH-07 | They need a finished setup and a known login |
| TC-AUTH-08 | TC-ACC-03 | It needs a user created with "Require password change at first sign-in" ticked |
| TC-ACC-03 | (pair with TC-AUTH-08) | Create users A and B here, then sign in as them in TC-AUTH-08 |
| TC-ACC-04, 05, 07, 09, 10 | TC-ACC-01 | They need the Staff user |
| TC-ACC-06 | TC-ACC-01, TC-AUTH-08 | After a reset the user sees the forced password change |
| TC-ACC-08 | TC-ROL-01 | Needs a role `qa-accounts` and a user with it, made the same way |
| TC-ROL-04 | TC-ROL-01, TC-ACC-01 | Needs the role `qa-view` and a user with it |
| TC-ROL-05, TC-DASH-08, TC-SS-04, TC-HIS-01, TC-PLG-07, TC-NCPA-08, TC-RPT-07, TC-LOG-05, TC-MNT-09 | TC-ACC-01 | They use the Staff user |
| TC-ROL-06, TC-SHL-10 | TC-ROL-01 | Each needs a role with one permission and a user with it, made the same way |
| TC-AUTH-11 | TC-ACC-01 | A registered user must exist |
| TC-SHL-09 | TC-AUTH-11 | It reads the password request made there |
| TC-SHL-06 | TC-ROL-04 | It uses the dashboard-only user |
| TC-SET-01 to 06 | TC-AUTH-07 | They need a Super Admin sign-in |
| TC-MNT-10, TC-SHL-08 | TC-SET-07 | They need working email |
| TC-DSC-02 to 05, 08, 09 | TC-DSC-01 | They need a scan that has found devices |
| TC-DSC-06 | TC-DSC-01 | Needs two networks with devices |
| TC-DSC-07 | TC-DSC-01, TC-PLG-03 | Needs a monitored port that you then close |
| TC-PLG-03 | TC-DSC-01 | Enabling a plugin needs discovered devices |
| TC-PLG-04, 05, 06 | TC-PLG-03 | They need an enabled plugin with services |
| TC-DI-01 to 04, 11 to 13, TC-TOP-01 to 06 | TC-DSC-01 | They need discovered devices |
| TC-DI-05 to 09, TC-DX-01 to 05 | TC-PLG-03 | They need monitored ports and the plugins for them |
| TC-DX-06, 07 | TC-DSC-01 | Need a device that answers SNMP |
| TC-NH-06 | TC-DX-07 | An interface must already be monitored |
| TC-DI-10 | TC-NCPA-04 | The NCPA port is protected only after a deployment |
| TC-DI-14, 15 | TC-DI-13 | They use a paused device |
| TC-DASH-02 | TC-DI-13 | The pause is made there |
| TC-DI-16 to 19 | TC-DSC-01 | Need identity review items (two records for one device) |
| TC-DASH-03 | TC-DSC-01, TC-PLG-03 | You need monitored services to break |
| TC-ACK-01, 03, 04, 06, 07, 08 | TC-DASH-03 | They need active alerts |
| TC-ACK-02 | TC-ROL-04, TC-DASH-03 | Needs the dashboard-only user and an active alert |
| TC-ACK-05 | TC-ACK-01 | An acknowledgement must exist to remove |
| TC-HIS-02 to 08 | TC-ACK-08, TC-SET-07 | Alert and notification events must exist |
| TC-SHL-07 | TC-DSC-02 | The bell needs a new notification, such as a finished scan |
| TC-MNT-03 to 06 | TC-MNT-02 | They reuse the same form |
| TC-MNT-07 | TC-MNT-02 | A window must exist to cancel |
| TC-MNT-08 | TC-MNT-07 | Same cancel flow, with Nagios stopped |
| TC-NCPA-02 | TC-DSC-01, TC-NCPA-01 | Needs a discovered Linux VM and `check_ncpa` enabled |
| TC-NCPA-03 | TC-NCPA-02 | The wizard is open from there |
| TC-NCPA-04 | TC-NCPA-03 | Needs a correct login |
| TC-NCPA-05, 06, 07, 10 | TC-NCPA-04 | They need a finished (or failed) deployment |
| TC-NCPA-09 | TC-NCPA-02 | Needs a trusted host key |
| TC-NCPA-11 | TC-NCPA-04, TC-NCPA-09 | Needs a deployed device with remote restart set |
| TC-DASH-09, TC-SS-05 | TC-NCPA-04 | Need NCPA data for about 3 days |
| TC-REM-01, 03, 04, 05 | TC-REM-02 | They need an action to look at or change |
| TC-REM-07, 08, 09 | TC-REM-02, TC-PLG-03 | They need an action and a service to break |
| TC-REM-06 | TC-REM-07, TC-REM-09 | The run log needs runs and skipped runs |
| TC-RPT-01 to 06 | TC-DASH-03, TC-ACK-08, TC-MNT-10 | A report needs incident data |
| TC-RPT-05 | TC-RPT-03, TC-RPT-04 | The exports must exist |
| TC-LOG-02 to 04 | TC-ACC-01, TC-DSC-02 | Log entries must exist |
| TC-DASH-06, TC-MNT-08, TC-SET-08 | everything above | They stop Nagios or break its config, so run them last and restore |
| TC-NFR-08, 09 | TC-DSC-01 | Need 10 and 15 monitored hosts |
| TC-NFR-10 | TC-DASH-03 | Needs a target to break |
| TC-EDG-01 to 18 | TC-ACC-01, TC-DSC-01, TC-DI-13 | They reuse the accounts, scans, and devices from earlier phases |

**Order-of-events cases (TC-SEQ) need first**

| Case | Do these first | Why |
| --- | --- | --- |
| TC-SEQ-01, 02, 06, 23 | TC-DASH-03, TC-PLG-03 | You need a monitored service to stop and start |
| TC-SEQ-03, 04, 05 | TC-MNT-02, TC-SET-07 | You need the window form and working email |
| TC-SEQ-06, 07 | TC-DI-13 | Pause and resume work |
| TC-SEQ-08, 24 | TC-DSC-02 | A scan can be started |
| TC-SEQ-09 | a fresh appliance | `check_http` disabled and no scan yet |
| TC-SEQ-10, 11 | TC-PLG-03, TC-DI-05 | A plugin is monitoring a port |
| TC-SEQ-12 | TC-ROL-04 | The role `qa-view` and its user exist |
| TC-SEQ-13 | TC-ROL-01 | Make a role with two permissions and a user |
| TC-SEQ-14, 15 | TC-ACC-01 | The Staff user exists |
| TC-SEQ-16 | TC-ACC-03 | A user with the forced change exists |
| TC-SEQ-17 | a fresh appliance | The bootstrap login is not used yet |
| TC-SEQ-18, 19, 20 | TC-REM-02, TC-PLG-03 | An action and a service to break |
| TC-SEQ-21 | TC-NCPA-04 | A deployed NCPA device |
| TC-SEQ-22 | TC-NCPA-09, TC-REM-10, TC-NCPA-04 | A deployed device with remote restart set |

