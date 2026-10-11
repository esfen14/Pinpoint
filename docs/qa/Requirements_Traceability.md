# Requirements Traceability

| ID | Source Spec/Journey | ISO Characteristic | Env | Verification | Status | Notes |
|---|---|---|---|---|---|---|
| J1-01 | QA_Test_Plan.md | RE | VM | agent | untested | |
| J1-02 | QA_Test_Plan.md | FS | VM | agent | untested | |
| J1-03 | QA_Test_Plan.md | SE | VM | agent | untested | |
| J1-04 | QA_Test_Plan.md | SE | VM | agent | untested | Admin Playwright login/dashboard smoke does not inspect the stored password hash; hash verification remains unexecuted |
| J1-05 | QA_Test_Plan.md | IC | VM | agent | untested | |
| J1-06 | QA_Test_Plan.md | FS | MANUAL | HUMAN | untested | |
| J1-07 | QA_Test_Plan.md | SE | VM | agent | untested | |
| J2-01 | QA_Test_Plan.md | FS | VM | agent | untested | |
| J2-02 | QA_Test_Plan.md | RE | VM | agent (UI) | untested | |
| J2-03 | QA_Test_Plan.md | FS | VM | agent | untested | API identifiers/ports passed; browser drawer not exercised |
| J2-04 | QA_Test_Plan.md | FS | VM | agent | untested | SSH plugin enablement observed; complete per-host before/after assertion not established |
| J2-05 | QA_Test_Plan.md | RE | VM | agent | untested | Live changed-network case not completed |
| J2-06 | QA_Test_Plan.md | IC | VM | agent | untested | Discovery stop returned terminal Interrupted; the required UI progress/cancellation and System Logs assertions remain unexecuted |
| J2-07 | QA_Test_Plan.md | FS | VM | agent | untested | Pause/resume API passed; UI/config/count assertions not exercised |
| J2-08 | QA_Test_Plan.md | RE | VM | agent | untested | Conflict review endpoint passed; full two-rescan baseline comparison not captured |
| J2-09 | QA_Test_Plan.md | FS | VM | agent | untested | Existing 8080 rows prevented a clean first-insertion claim |
| J2-10 | QA_Test_Plan.md | RE | MOCK | agent | untested | |
| J2-11 | QA_Test_Plan.md | RE | MOCK | agent | untested | |
| J3-01 | QA_Test_Plan.md | FS | VM | agent (UI) | untested | |
| J3-02 | QA_Test_Plan.md | FS | VM | agent | pass | Live deployment to two authorized targets succeeded; see 2026-10-11 j2-j3-dry-run report |
| J3-03 | QA_Test_Plan.md | SE | VM | agent | untested | API response contained no password; database inspection not performed |
| J3-04 | QA_Test_Plan.md | SE | VM | agent | untested | |
| J3-05 | QA_Test_Plan.md | RE | VM | agent | untested | check_ncpa was not enabled before the deployment run |
| J3-06 | QA_Test_Plan.md | SE | VM | agent | pass | Deployment log recorded actor, time, outcome and progress; see report |
| J3-07 | QA_Test_Plan.md | RE | VM | agent | untested | |
| J3-08 | QA_Test_Plan.md | RE | VM | agent | untested | |
| J3-09 | QA_Test_Plan.md | RE | VM | agent | untested | Required before/after identity baseline was not captured for this deployment |
| J3-10 | QA_Test_Plan.md | RE | MOCK | agent | untested | |
| J4-01 | QA_Test_Plan.md | FS | VM | agent | untested | |
| J4-02 | QA_Test_Plan.md | FS | VM | agent | untested | |
| J4-03 | QA_Test_Plan.md | FS | VM | agent | untested | |
| J4-04 | QA_Test_Plan.md | RE | VM | agent | untested | |
| J4-05 | QA_Test_Plan.md | SE | VM | agent | untested | |
| J4-06 | QA_Test_Plan.md | FS | VM | agent · destructive | untested | |
| J4-07 | QA_Test_Plan.md | FS | VM | agent | untested | |
| J4-08 | QA_Test_Plan.md | FS | MOCK | agent | untested | |
| J5-01 | QA_Test_Plan.md | RE | VM | agent · destructive | untested | |
| J5-02 | QA_Test_Plan.md | FS | VM | agent · destructive | untested | |
| J5-03 | QA_Test_Plan.md | FS | VM | agent · destructive | untested | |
| J5-04 | QA_Test_Plan.md | FS | VM | agent · destructive | untested | |
| J5-05 | QA_Test_Plan.md | RE | VM | agent · destructive | untested | |
| J5-06 | QA_Test_Plan.md | RE | VM | agent · destructive | untested | |
| J5-07 | QA_Test_Plan.md | RE | VM | agent · destructive | untested | |
| J5-08 | QA_Test_Plan.md | FS | MOCK | agent | untested | |
| J5-10 | QA_Test_Plan.md | IC | VM | agent (UI) | untested | |
| J5-11 | QA_Test_Plan.md | FS | VM | HUMAN | untested | |
| J5-09 | QA_Test_Plan.md | SE | MOCK | agent | untested | |
| J6-01 | QA_Test_Plan.md | FS | VM | agent · destructive | untested | |
| J6-02 | QA_Test_Plan.md | FS | VM | agent · destructive | untested | |
| J6-03 | QA_Test_Plan.md | FS | VM | agent | untested | |
| J6-04 | QA_Test_Plan.md | FS | VM | agent | untested | |
| J6-05 | QA_Test_Plan.md | SE | VM | agent | untested | |
| J7-01 | QA_Test_Plan.md | FS | VM | agent | untested | |
| J7-02 | QA_Test_Plan.md | FS | VM | agent | untested | |
| J7-03 | QA_Test_Plan.md | FS | VM | agent | untested | |
| J7-04 | QA_Test_Plan.md | IC | VM | agent | untested | |
| J7-05 | QA_Test_Plan.md | IC | VM | agent | untested | |
| J7-06 | QA_Test_Plan.md | FS | VM | agent | untested | |
| J7-07 | QA_Test_Plan.md | FS | VM | agent | untested | |
| J7-08 | QA_Test_Plan.md | FS | VM | agent | untested | |
| J7-09 | QA_Test_Plan.md | FS | MOCK | agent | untested | |
| J8-01 | QA_Test_Plan.md | FS | VM | agent | untested | |
| J8-02 | QA_Test_Plan.md | FS | VM | agent | untested | |
| J8-03 | QA_Test_Plan.md | FS | VM | agent | untested | |
| J8-04 | QA_Test_Plan.md | FS | VM | agent | untested | |
| J8-05 | QA_Test_Plan.md | IC | VM | HUMAN | untested | |
| J8-06 | QA_Test_Plan.md | SE | VM | agent | untested | |
| J8-07 | QA_Test_Plan.md | IC | VM | agent | untested | |
| J9-01 | QA_Test_Plan.md | FS | VM | agent | untested | |
| J9-02 | QA_Test_Plan.md | FS | VM | agent | untested | |
| J9-03 | QA_Test_Plan.md | SE | MOCK | agent | untested | |
| J9-04 | QA_Test_Plan.md | SE | VM | agent | untested | |
| J9-05 | QA_Test_Plan.md | SE | VM | agent | untested | |
| J9-06 | QA_Test_Plan.md | IC | VM | agent | untested | |
| J9-07 | QA_Test_Plan.md | SE | VM | agent | untested | |
| J9-08 | QA_Test_Plan.md | IC | VM | agent | untested | |
| J9-09 | QA_Test_Plan.md | FS | VM | agent | untested | |
| J9-10 | QA_Test_Plan.md | SE | MOCK | agent | untested | |
| J9-11 | QA_Test_Plan.md | SE | MOCK | agent | untested | |
| J9-12 | QA_Test_Plan.md | SE | MOCK | agent | untested | |
| X1-01 | QA_Test_Plan.md | IC | VM | agent | untested | |
| X2-01 | QA_Test_Plan.md | SE | VM | agent | untested | |
| X3-01 | QA_Test_Plan.md | FS | VM | agent | untested | |
| X3-02 | QA_Test_Plan.md | FS | VM | agent · destructive | untested | |
| X3-03 | QA_Test_Plan.md | FS | VM | agent | untested | |
| X4-01 | QA_Test_Plan.md | SE | VM | agent | untested | |
| X5-01 | QA_Test_Plan.md | RE | VM | agent | untested | |
| PT-01 | QA_Test_Plan.md | PE | VM | agent | untested | |
| PT-02 | QA_Test_Plan.md | PE | MOCK | agent | untested | |
| PT-03 | QA_Test_Plan.md | PE | VM | agent | untested | |
| PT-04 | QA_Test_Plan.md | PE | VM | agent · destructive | untested | |
| PT-05 | QA_Test_Plan.md | RE | VM | agent | untested | |
| PT-06 | QA_Test_Plan.md | PE | VM | agent | untested | |

| **Acceptance** | | | | | | |
|---|---|---|---|---|---|---|
| BB-01 | QA_Test_Plan.md §5 (Black-box acceptance) | FS | VM | agent (aggregate) | untested | Automated Nagios Deployment (Nagios Core installed and configured) |
| BB-02 | QA_Test_Plan.md §5 (Black-box acceptance) | FS | VM | agent (aggregate) | untested | Agent Installation (monitoring agent installed and configured automatically) |
| BB-03 | QA_Test_Plan.md §5 (Black-box acceptance) | FS | VM | agent (aggregate) | untested | Device Monitoring (system detects host availability and status) |
| BB-04 | QA_Test_Plan.md §5 (Black-box acceptance) | FS | VM | agent (aggregate) | untested | Service Monitoring (system displays service health and status) |
| BB-05 | QA_Test_Plan.md §5 (Black-box acceptance) | RE | VM | agent (aggregate) | untested | Alert Notification System (system generates alert notification) |
| BB-06 | QA_Test_Plan.md §5 (Black-box acceptance) | FS | VM | agent (aggregate) | untested | Network Discovery (structured view of the network) |
| BB-07 | QA_Test_Plan.md §5 (Black-box acceptance) | FS | VM | agent (aggregate) | untested | Dashboard Visualization (summarized network health information) |
