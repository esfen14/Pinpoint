# Test run: issue-218-signout

| | |
|---|---|
| Date | 2026-11-25 |
| Commit tested | `47c07fea` (owner run). The scripted run used the working tree before that commit; its product code is the same |
| Plan | TC-ACC-05 in the [case catalog](../../qa/Pinpoint%20-%20Black-Box%20Test%20Cases%20by%20Module%20with%20Traceability%20Matrix.md), as updated for [#218](https://github.com/esfen14/Pinpoint/issues/218) |
| Tester / executor mode | Mixed: human manual by the owner, plus an AI-assisted scripted Playwright run (Claude), listed separately below |
| Catalog revision and SHA-256 | `47c07fea`, `b341272a0d339d6ffa485a35e2ff2302da0abe3d4a6564cdd186532de11e9325` |
| Queue / set / session / batch | None; no supervised queue or card |
| Deployed application / installer revision | Local lab started from branch `issue-218-signout-warning`; backend as of `3897334e` (unchanged up to `47c07fea`), web client served by the Vite dev server from the working tree. No installer |
| Baseline / preflight / restoration | Fresh lab with seeded development data. The lab was removed with `scripts/lab down` afterwards |
| Start / end / time zone | Owner screenshots 19:01 to 19:02, UTC+8. Exact start and end of both runs not recorded |
| Environment | Local Docker lab ([Local Lab](../../manuals/Local_Lab.md)), lab network `10.78.0.0/24`, lab mail sink for email |
| Raw evidence | Three screenshots, attached to [this comment on #218](https://github.com/esfen14/Pinpoint/issues/218#issuecomment-7161120310); originals held by the lab owner in `/home/paeng/Pictures/Screenshots` (not committed) |

## Result

**Overall: Pass.** The owner reports seeing the expected result on the version
with the 10-second session check. The scripted run observed the expected items
on the same product code. Not covered: an installed appliance and delivery to a
real mailbox.

Totals (unique TC): Pass 1, Fail 0, Partial 0, Blocked 0, Inconclusive 0, Not run 0.
Totals (unique E2E): Pass 0, Fail 0, Partial 0, Blocked 0, Inconclusive 0, Not run 0.
Historical credit: 0 accepted, 0 partial.
Attempts and setup operations are not extra unique cases.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| TC-ACC-05 | Pass | Owner: dialog warning, session ended, page went to `/login`; three screenshots. Scripted run: see below | [#218](https://github.com/esfen14/Pinpoint/issues/218) |

## Owner screenshots

| File | What it shows |
|---|---|
| `Screenshot From 2026-11-25 19-01-24.png` | Emily Davis signed in on Settings; the sidebar lists only Settings |
| `Screenshot From 2026-11-25 19-01-42.png` | The sign-in page, with no message on it |
| `Screenshot From 2026-11-25 19-02-23.png` | Emily Davis signed in on Overview with the full sidebar; page time 07:02 PM |

The screenshots do not show the Edit Account dialog, the administrator's save or
how long the redirect took. The dialog line rests on the owner's report and the
scripted run. A sign-in page without a message is an observation, not a failure.

## Expected-item observations and restoration

Items are the expected results of TC-ACC-05 in order. E5 and E6 are notes about
the case, not requirements.

| Case / attempt | Expected item | Observed value | Verdict | Private evidence reference | Restoration verified |
|---|---|---|---|---|---|
| TC-ACC-05 / owner | E1 dialog line | Reported as expected | Pass (owner report) | None | Lab removed |
| TC-ACC-05 / owner | E2 session ends, page goes to `/login` | Reported as expected | Pass | Screenshots | Lab removed |
| TC-ACC-05 / scripted | E1 dialog line | "Changing the email, role, status or password signs the user out." visible | Pass | None kept | Lab removed |
| TC-ACC-05 / scripted | E2 session ends, page goes to `/login` | Idle page reached `/login` 7.9 to 9.9 s after a role, email, password or suspension change; a click on another page reached it in 0.3 s | Pass | None kept | Lab removed |
| TC-ACC-05 / scripted | E3 email or administrator message | Without email set up, the administrator was told. With the lab mail sink, role, email and password changes were emailed; password emails held no password | Pass | None kept | Lab removed |
| TC-ACC-05 / scripted | E4 suspended sign-in | "This account is suspended. Contact the admin for any concerns." | Pass | None kept | Lab removed |

## Scripted run

Playwright with a temporary script that is not committed, so it cannot be re-run
from the repository.

- First attempt: 15 of 15 checks passed. Besides the items above: the Inactive
  sign-in message stayed "Account inactive.", a name change appeared without
  sign-out, changing one's own password kept the session, and a forgot-password
  reset was emailed. Its click check clicked the page already open, so it showed
  only the timed check.
- Second attempt, for that gap: 1 of 1 passed (click on another page, 0.3 s).
- It used `daniel.wilson@test.com`, restored that account's role, status, name,
  email and password, and left Settings, Email pointed at the lab mail sink until
  the lab was removed.

## Deviations from the plan

- The case names the Staff user; the owner's screenshots use the seeded user
  Emily Davis, and the scripted run used another seeded Staff user.
- The earlier FAIL recorded for TC-ACC-05 is unchanged in the catalog. Its
  [disposition](https://github.com/esfen14/Pinpoint/issues/218#issuecomment-7159770550)
  is on #218.

## Follow-up

- Defects found: none.
- Cases to repeat in the next run: none required. An installed appliance and a
  real mailbox remain unverified.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
