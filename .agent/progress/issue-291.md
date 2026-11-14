# Issue #291: Write the missing topic guides that feed the User Manual

Branch: `sys-topic-guide` (user instruction: work on the current branch; do NOT commit or push)
Status: in-progress

## Finish condition

- [ ] One guide per missing area in `docs/manuals/`, from the page requirements and code, each with purpose, prerequisites, numbered steps, expected result and precautions; unverified items marked **TBC**: login/roles/accounts, Dashboard and Network Health, Device Inventory, Alerts and notification history, Plugin Manager, Network Discovery, Settings, System Logs, Topology.
- [ ] The guides are indexed in `docs/manuals/README.md`.
- [ ] Guides are written to be linked from the User Manual (#181), not duplicated in it.
- [ ] Every page in the web interface has a guide or an explicit TBC entry.

Requirement coverage:

| Issue requirement | Finish-condition item | Proof |
|---|---|---|
| Nine missing guides | item 1 | `ls docs/manuals`; read each |
| Index in docs/manuals/README.md | item 2 | file exists, links resolve (`check_doc_links.py`) |
| Link from the User Manual rather than duplicate | item 3 | Out of this change: the User Manual (#181) does not exist yet; guides are standalone and indexed |
| Every page has a guide or TBC entry | item 4 | route-by-route table in the index, checked against `App.tsx` |

## Plan

1. [x] Gather permissions, login, accounts, roles source; write `Login_Accounts_and_Roles.md`
2. [x] `Dashboard_and_Network_Health.md` (include Network Status page)
3. [x] `Device_Inventory.md` (links to Device_Identity_Review.md)
4. [x] `Alerts_and_Notification_History.md`
5. [x] `Plugin_Manager.md`
6. [x] `Network_Discovery.md`
7. [x] `Settings.md` (links to Email_Settings.md, Notification_Policy.md)
8. [x] `System_Logs.md` (links to Storage_and_Nagios_Logs.md)
9. [x] `Topology.md`
10. [x] `docs/manuals/README.md` index with a page-by-page table; link from docs/README.md
11. [x] `scripts/check_doc_links.py`, other docs checks

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | plan written | - | - |
| 2 | wrote nine guides, manuals/README.md index, docs/README.md link, Plugin Manager wording fix | check_doc_links.py; hand link check of docs/manuals | 284 docs, all links resolve; progress check OK |

## State for the next session

- Last check run (exact command): `python3 -I scripts/check_doc_links.py .`
- Result: green
- Hypothesis: documentation only; nothing can be run against a live UI here, so every guide carries a TBC verification note
- Next action: user review; nothing committed. Delete this file before a ready PR.

## Decisions and notes

- Nothing is committed or pushed (user instruction). Delete this file before a pull request is marked ready.
- The issue comment from an outside user suggests a trial in a third-party writing tool with uploaded files. Not used: it sends project content to an external service and is not part of the issue's tasks.
