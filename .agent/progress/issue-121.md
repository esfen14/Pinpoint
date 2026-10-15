# Issue #121: Local and remote service recovery actions with restricted sudo rule

Branch: `issue-121-local-service-restart`
Status: in-progress

## Finish condition

Scope this session (agreed with the user): Part 8.1 only. Parts 8.2 and 8.3 stay open (see notes).

- [ ] 8.1 A unit outside the fixed list is rejected with 400 at creation and refused at run time.
- [ ] 8.1 A hard failure of a covered check triggers at most one restart within the cooldown; run recorded with exit code.
- [ ] 8.1 Maintenance Mode and the hourly cap block the restart and record why.
- [ ] 8.1 No shell is used; output contains no secrets.
- [ ] 8.1 Permitted units exposed through the actions API.
- [ ] 8.2 sudo rule / visudo / upgrade handling (OUT OF THIS SESSION: installer code not in repo)
- [ ] 8.3 design note and remote restart (OUT OF THIS SESSION: needs investigation and security decision)

Requirement coverage:

| Issue requirement | Finish-condition item | Proof |
|---|---|---|
| fixed unit list, 400 at creation | 8.1 unit rejected | test_remediation_actions.py, test_remediation_routes |
| argument-list sudo -n systemctl restart, timeout, exit code | 8.1 restart + exit code | test_remediation_actions.py (subprocess mocked) |
| refuse on Maintenance Mode / cooldown / cap, record reason | 8.1 blocks | test_remediation_actions.py, test_remediation_consumer.py |
| units in actions API | 8.1 API | test_remediation_actions.py describe_types |
| 8.2, 8.3 | deferred | not proven; follow-up issues |

## Plan

1. [x] Tests then `restart_local_service` type with fixed unit list (server/app/remediation_actions.py, server/tests/unit/test_remediation_actions.py)
2. [x] Route test: 400 on bad unit, units listed in API (server/tests/unit/ remediation routes test)
3. [x] Consumer test: cooldown/cap with this type (server/tests/unit/test_remediation_consumer.py)
4. [x] Specs: Backend_Modules_and_Routes.md, Data_Model_and_Integrations.md, Implementation_Status.md
5. [ ] verify.sh backend and docs, finish

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | restart_local_service type, ActionFailed, maintenance flag in RunContext, enum + migration b8e3d5f2a417, tests, specs | pytest remediation unit files | green |

## State for the next session

- Last check run: scripts/verify.sh backend
- Result: 3155 passed, 78 failed, 36 errors, none in remediation files; a sample of 5 failing files (migration round trips, automation, host recipients) also fails on a clean origin/main checkout on this Windows machine (10 failed). Not all 114 were compared. verify.sh docs fails only on a Windows path-separator assertion in scripts/test_qa_queue.py (unrelated)
- Hypothesis: n/a
- Next action: draft PR open; wait for CI on Linux, then Parts 8.2/8.3 after decisions

## Decisions and notes

- Maintenance Mode refusal is recorded as outcome `failed` with a "Refused" message, because a new outcome would need a migration and frontend change the issue marks N/A. Downside: a refused run counts toward the hourly cap. Raise with a person.
- 8.2: installer location is not in this repo; no sudoers drop-in written.
- 8.3: needs design note first; not started.
- Migration was needed after all: Action_Type is a DB Enum, so adding the member required b8e3d5f2a417 (issue said N/A).
- Remediation form does not render action parameters; `unit` is settable only via API. Frontend change left out of scope.
