# Current-case automation coverage

Generated from `automation-coverage.json`; source implementation is not a runtime result.
No case is certified PASS here. Human catalog verdicts and historical report credit remain separate.
An implemented adapter still needs reviewed live cards, environment/preflight, exact launcher support and explicit start.
Assertion markers and source hashes support review; they do not prove assertion correctness or live behavior.

| Case | Module | Source coverage / executor | Adapter | Missing expected items | Next work |
|---|---|---|---|---|---|
| TC-AUTH-05 | AUTH | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-AUTH-06 | AUTH | unmapped / unassigned | None | E1, E2, E3, E4 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-AUTH-07 | AUTH | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-AUTH-01 | AUTH | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-AUTH-02 | AUTH | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-AUTH-03 | AUTH | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-AUTH-04 | AUTH | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-AUTH-09 | AUTH | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-AUTH-12 | AUTH | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-ROL-01 | ROL | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-ROL-02 | ROL | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-ROL-03 | ROL | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-ACC-01 | ACC | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-ACC-02 | ACC | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-ACC-03 | ACC | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-AUTH-08 | AUTH | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-ACC-04 | ACC | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-ACC-05 | ACC | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-ACC-06 | ACC | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-ACC-07 | ACC | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-ACC-09 | ACC | implemented / scripted automation | [TC-ACC-09: The accounts page needs permission](../../client/e2e/qa-permissions.lab.spec.ts) | None in source review | Source adapter complete; bounded live launcher support, new reviewed queue/card, current prerequisites and separate explicit start remain required. |
| TC-ACC-10 | ACC | partial / scripted automation | [TC-ACC-10: Add User uses the default role](../../client/e2e/qa-modules-2-9.lab.spec.ts) | E3 | E1 and E2 have a source adapter. E3 requires the live role-options list to have no active roles; this issue will not deactivate system roles to manufacture that state. Created account rows and audit entries persist after deactivation, so the current bounded baseline cannot certify restoration; the live card remains blocked pending a separately reviewed disposable-appliance recovery plan. |
| TC-ACC-08 | ACC | implemented / scripted automation | [TC-ACC-08: "Send this user email alerts" depends on permission](../../client/e2e/qa-modules-2-9.lab.spec.ts) | None in source review | Source adapter is complete for every catalog expected item; live launcher support, reviewed current lab prerequisites/cards and a separate explicit start are still required. |
| TC-ROL-04 | ROL | implemented / scripted automation | [TC-ROL-04: A dashboard-only user is limited to the Dashboard](../../client/e2e/qa-modules-2-9.lab.spec.ts) | None in source review | Source adapter is complete for every catalog expected item; live launcher support, reviewed current lab prerequisites/cards and a separate explicit start are still required. |
| TC-ROL-05 | ROL | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-ROL-06 | ROL | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-AUTH-10 | AUTH | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-AUTH-11 | AUTH | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SHL-09 | SHL | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SHL-04 | SHL | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SHL-10 | SHL | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DASH-08 | DASH | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SS-04 | SS | implemented / scripted automation | [TC-SS-04: System Status needs permission](../../client/e2e/qa-permissions.lab.spec.ts) | None in source review | Source adapter complete; live launcher integration, reviewed cards, target/preflight and runtime proof remain pending. |
| TC-HIS-01 | HIS | implemented / scripted automation | [TC-HIS-01: History needs permission](../../client/e2e/qa-permissions.lab.spec.ts) | None in source review | Source adapter complete; live launcher integration, reviewed cards, target/preflight and runtime proof remain pending. |
| TC-PLG-07 | PLG | implemented / scripted automation | [TC-PLG-07: Plugins need permission](../../client/e2e/qa-permissions.lab.spec.ts) | None in source review | Source adapter complete; live launcher integration, reviewed cards, target/preflight and runtime proof remain pending. |
| TC-NCPA-08 | NCPA | implemented / scripted automation | [TC-NCPA-08: NCPA Deployment needs permission](../../client/e2e/qa-permissions.lab.spec.ts) | None in source review | Source adapter complete; bounded live launcher support, new reviewed queue/card, current prerequisites and separate explicit start remain required. |
| TC-RPT-07 | RPT | implemented / scripted automation | [TC-RPT-07: Reports need permission](../../client/e2e/qa-permissions.lab.spec.ts) | None in source review | Source adapter complete; live launcher integration, reviewed cards, target/preflight and runtime proof remain pending. |
| TC-LOG-05 | LOG | implemented / scripted automation | [TC-LOG-05: System Logs need permission](../../client/e2e/qa-permissions.lab.spec.ts) | None in source review | Source adapter complete; live launcher integration, reviewed cards, target/preflight and runtime proof remain pending. |
| TC-SHL-06 | SHL | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-NFR-01 | NFR | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-NFR-02 | NFR | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SET-07 | SET | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SET-01 | SET | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SET-02 | SET | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SET-03 | SET | unmapped / unassigned | None | E1, E2, E3, E4 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SET-04 | SET | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SET-05 | SET | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SET-06 | SET | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SHL-01 | SHL | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SHL-02 | SHL | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SHL-03 | SHL | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DSC-01 | DSC | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DSC-02 | DSC | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DSC-03 | DSC | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DSC-04 | DSC | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DSC-05 | DSC | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DSC-08 | DSC | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DSC-09 | DSC | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-PLG-01 | PLG | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-PLG-02 | PLG | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-PLG-03 | PLG | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-PLG-04 | PLG | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-PLG-05 | PLG | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-PLG-06 | PLG | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DI-01 | DI | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DI-02 | DI | implemented / scripted automation | [TC-DI-02: Port groups and their order](../../client/e2e/qa-modules-2-9.lab.spec.ts) | None in source review | Source adapter covers every catalog expected item with read-only browser assertions; current live launcher, reviewed current prerequisites/cards and a separate explicit start are still required. |
| TC-DI-03 | DI | implemented / scripted automation | [TC-DI-03: One reason per port](../../client/e2e/qa-modules-2-9.lab.spec.ts) | None in source review | Source adapter covers every catalog expected item with read-only browser assertions; current live launcher, reviewed current prerequisites/cards and a separate explicit start are still required. |
| TC-DI-04 | DI | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DASH-01 | DASH | unmapped / unassigned | None | E1, E2, E3, E4 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DASH-05 | DASH | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DASH-07 | DASH | implemented / scripted automation | [TC-DASH-07: "No data" instead of blank cards](../../client/e2e/qa-modules-2-9.lab.spec.ts) | None in source review | Source adapter covers each catalog expected item using read-only Dashboard assertions; current live launcher, reviewed current data prerequisites/cards and a separate explicit start are still required. |
| TC-NH-01 | NH | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-NH-02 | NH | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-NH-03 | NH | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-NH-04 | NH | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-NH-05 | NH | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SS-01 | SS | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SS-02 | SS | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SS-03 | SS | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DX-01 | DX | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DX-02 | DX | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DX-03 | DX | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DX-04 | DX | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DX-05 | DX | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DX-06 | DX | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DX-07 | DX | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DX-08 | DX | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DX-09 | DX | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DX-10 | DX | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-NH-06 | NH | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-NH-07 | NH | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-TOP-01 | TOP | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-TOP-02 | TOP | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-TOP-03 | TOP | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-TOP-04 | TOP | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-TOP-05 | TOP | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-TOP-06 | TOP | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DI-05 | DI | unmapped / unassigned | None | E1, E2, E3, E4 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DI-06 | DI | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DI-07 | DI | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DI-08 | DI | implemented / scripted automation | [TC-DI-08: The Checked by line](../../client/e2e/qa-modules-2-9.lab.spec.ts) | None in source review | Source adapter covers all catalog items using existing TCP/UDP fixtures, blocks port mutations, and closes both dialogs without saving; live fixture/card/preflight and explicit start remain required. |
| TC-DI-09 | DI | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DI-11 | DI | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DI-12 | DI | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DI-13 | DI | unmapped / unassigned | None | E1, E2, E3, E4 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DASH-02 | DASH | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DI-14 | DI | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DI-15 | DI | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DI-16 | DI | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DI-17 | DI | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DI-18 | DI | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DI-19 | DI | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DSC-06 | DSC | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DSC-07 | DSC | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DASH-03 | DASH | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-ACK-01 | ACK | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-ACK-02 | ACK | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-ACK-03 | ACK | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-ACK-04 | ACK | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-ACK-05 | ACK | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-ACK-06 | ACK | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-ACK-07 | ACK | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-ACK-08 | ACK | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DASH-04 | DASH | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-HIS-02 | HIS | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-HIS-03 | HIS | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-HIS-04 | HIS | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-HIS-05 | HIS | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-HIS-06 | HIS | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-HIS-07 | HIS | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-HIS-08 | HIS | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SHL-07 | SHL | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SHL-08 | SHL | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-MNT-01 | MNT | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-MNT-02 | MNT | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-MNT-03 | MNT | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-MNT-04 | MNT | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-MNT-05 | MNT | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-MNT-06 | MNT | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-MNT-07 | MNT | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-MNT-09 | MNT | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-MNT-10 | MNT | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-NCPA-01 | NCPA | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-NCPA-02 | NCPA | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-NCPA-03 | NCPA | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-NCPA-04 | NCPA | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-NCPA-05 | NCPA | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-NCPA-06 | NCPA | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-NCPA-07 | NCPA | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-NCPA-09 | NCPA | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-NCPA-10 | NCPA | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-NCPA-11 | NCPA | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DI-10 | DI | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DASH-09 | DASH | unmapped / unassigned | None | E1, E2, E3, E4, E5 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SS-05 | SS | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-REM-02 | REM | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-REM-01 | REM | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-REM-04 | REM | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-REM-03 | REM | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-REM-05 | REM | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-REM-07 | REM | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-REM-09 | REM | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-REM-06 | REM | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-REM-08 | REM | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-REM-10 | REM | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-RPT-01 | RPT | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-RPT-02 | RPT | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-RPT-03 | RPT | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-RPT-04 | RPT | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-RPT-05 | RPT | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-RPT-06 | RPT | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-LOG-01 | LOG | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-LOG-02 | LOG | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-LOG-03 | LOG | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-LOG-04 | LOG | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SHL-05 | SHL | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-DASH-06 | DASH | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-MNT-08 | MNT | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SET-08 | SET | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SET-09 | SET | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-NFR-03 | NFR | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-NFR-04 | NFR | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-NFR-05 | NFR | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-NFR-06 | NFR | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-NFR-07 | NFR | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-NFR-08 | NFR | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-NFR-09 | NFR | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-NFR-10 | NFR | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-NFR-11 | NFR | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-EDG-01 | EDG | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-EDG-02 | EDG | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-EDG-03 | EDG | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-EDG-04 | EDG | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-EDG-05 | EDG | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-EDG-06 | EDG | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-EDG-07 | EDG | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-EDG-08 | EDG | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-EDG-09 | EDG | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-EDG-10 | EDG | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-EDG-11 | EDG | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-EDG-12 | EDG | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-EDG-13 | EDG | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-EDG-14 | EDG | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-EDG-15 | EDG | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-EDG-16 | EDG | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-EDG-17 | EDG | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-EDG-18 | EDG | unmapped / unassigned | None | E1 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SEQ-01 | SEQ | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SEQ-02 | SEQ | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SEQ-03 | SEQ | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SEQ-04 | SEQ | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SEQ-05 | SEQ | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SEQ-06 | SEQ | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SEQ-07 | SEQ | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SEQ-08 | SEQ | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SEQ-10 | SEQ | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SEQ-11 | SEQ | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SEQ-12 | SEQ | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SEQ-13 | SEQ | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SEQ-14 | SEQ | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SEQ-15 | SEQ | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SEQ-16 | SEQ | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SEQ-18 | SEQ | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SEQ-19 | SEQ | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SEQ-20 | SEQ | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SEQ-21 | SEQ | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SEQ-22 | SEQ | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SEQ-23 | SEQ | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SEQ-24 | SEQ | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SEQ-09 | SEQ | unmapped / unassigned | None | E1, E2 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| TC-SEQ-17 | SEQ | unmapped / unassigned | None | E1, E2, E3 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| E2E-01 | E2E | unmapped / unassigned | None | E1, E2, E3, E4 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| E2E-02 | E2E | unmapped / unassigned | None | E1, E2, E3, E4, E5, E6, E7 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| E2E-03 | E2E | unmapped / unassigned | None | E1, E2, E3, E4, E5, E6 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| E2E-04 | E2E | unmapped / unassigned | None | E1, E2, E3, E4, E5, E6, E7, E8 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| E2E-05 | E2E | unmapped / unassigned | None | E1, E2, E3, E4, E5, E6 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| E2E-06 | E2E | unmapped / unassigned | None | E1, E2, E3, E4, E5 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| E2E-07 | E2E | unmapped / unassigned | None | E1, E2, E3, E4, E5, E6, E7 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |
| E2E-08 | E2E | unmapped / unassigned | None | E1, E2, E3, E4, E5 | No source-reviewed current-case adapter; fixture, observations and recovery need assessment. |

Source register: 13 implemented, 1 partial, 225 unmapped (TC and E2E combined; not execution counts).
