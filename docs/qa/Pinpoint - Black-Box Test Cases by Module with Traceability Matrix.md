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

## Test cases: access and security

### Module 1 – Authentication (login page, first-run setup, session)

**Summary of cases**

| TC | Case | Req | Tech | Pri | Result |
| --- | --- | --- | --- | --- | --- |
| TC-AUTH-01 | Valid sign-in | AUTH-01 | EP | H | PASS |
| TC-AUTH-02 | Wrong password is refused | AUTH-02 | EP | H | PASS |
| TC-AUTH-03 | Unknown email gives the same message | AUTH-02 | EP | H | PASS |
| TC-AUTH-04 | Empty fields are refused | AUTH-02 | EG | M | PASS |
| TC-AUTH-05 | First-run setup cannot be skipped | AUTH-03 | ST | H | PASS |
| TC-AUTH-06 | Setup rejects a bad email or password | AUTH-03 | EP | H | PASS |
| TC-AUTH-07 | Valid setup completes | AUTH-03 | EP | H | PASS |
| TC-AUTH-08 | Forced password change | AUTH-04 | ST | H | PASS |
| TC-AUTH-09 | Sign out asks for confirmation | AUTH-05 | ST | M | PASS |
| TC-AUTH-10 | Idle session timeout | AUTH-06 | BVA | M | PASS |
| TC-AUTH-11 | Forgot Password request | AUTH-07 | EP | M | PASS |
| TC-AUTH-12 | Routes redirect to login | AUTH-08 | EG | M | PASS |

#### TC-AUTH-01 – Valid sign-in

**Requirement:** REQ-AUTH-01 · **Technique:** EP · **Priority:** H · **Result:** PASS

**Before you start:** a Super Admin account whose first-run setup is finished. You are signed out.

**Steps**

1. Open the Pinpoint address in the browser. It goes to `/login` ("Log In to your Account").
2. In **Email** type the Super Admin email. In **Password** type its password. Leave **Remember me** unticked.
3. Press the login button.
4. In a new tab open `/api/user/me`.

**Expected result**

- The Overview (Dashboard) page opens.
- `/api/user/me` shows the signed-in user's details.

#### TC-AUTH-02 – Wrong password is refused

**Requirement:** REQ-AUTH-02 · **Technique:** EP · **Priority:** H · **Result:** PASS

**Steps**

1. Sign out if needed and open `/login`.
2. Type the Super Admin email and a wrong password.
3. Press the login button.
4. In a new tab open `/api/user/me`.

**Expected result**

- An error message appears and you stay on `/login`.
- `/api/user/me` returns 401 (you are not signed in).

#### TC-AUTH-03 – Unknown email gives the same message

**Requirement:** REQ-AUTH-02 · **Technique:** EP · **Priority:** H · **Result:** PASS

**Steps**

1. On `/login` type an email that is not registered, such as `nobody@mail-lab.com`, and any password.
2. Press the login button and write down the exact message.
3. Repeat TC-AUTH-02 and compare the two messages.

**Expected result**

- The two messages are identical, so the page does not reveal whether the email or the password was wrong.
- No session is created.

#### TC-AUTH-04 – Empty fields are refused

**Requirement:** REQ-AUTH-02 · **Technique:** EG · **Priority:** M · **Result:** PASS

**Steps**

1. On `/login` leave both fields empty and press the login button.
2. Type only an email, leave **Password** empty, and press the login button again.

**Expected result**

- Both attempts are refused with a message.
- No session is created.

#### TC-AUTH-05 – First-run setup cannot be skipped

**Requirement:** REQ-AUTH-03 · **Technique:** ST · **Priority:** H · **Result:** PASS

**Before you start:** a fresh install whose generated bootstrap login has not been used yet.

**Steps**

1. Sign in with the bootstrap email and password.
2. Read the window **Finish setting up Pinpoint**.
3. Try to close it (Escape key, clicking outside it).
4. Type `/dashboard` in the address bar and press Enter.
5. In a new tab open `/api/user/accounts`.

**Expected result**

- The setup window covers the whole page and cannot be closed. The only way out is **Sign out**.
- `/dashboard` still shows the setup window.
- `/api/user/accounts` returns 403 until setup is finished.

#### TC-AUTH-06 – Setup rejects a bad email or password

**Requirement:** REQ-AUTH-03 · **Technique:** EP · **Priority:** H · **Result:** PASS

**Before you start:** the setup window from TC-AUTH-05 is open.

**Steps**

1. Fill **Current password** with the bootstrap password.
2. **Reserved email domain:** in **New email** type `ops@company.test`. Fill a valid **New password** and **Confirm new password**. Press **Complete setup**.
3. **Weak password:** change **New email** to a real-looking domain such as `ops@mail-lab.com`. Type the password `short1!` in both password boxes and submit.
4. **Mismatch:** type `Lab-Pinpoint-2026!` in **New password** and `Lab-Pinpoint-2027!` in **Confirm new password**.

**Expected result**

- Step 2: refused with a message that the domain (`test`) is reserved and cannot receive email. The domains `local`, `lan`, `test`, `example`, `invalid`, `localhost`, `internal`, `home.arpa`, and `pinpoint.lan` are all refused.
- Step 3: refused with a password rule message (12 or more characters with upper and lower case, a number, and a symbol when the strong policy is on, or at least 8 characters when it is off).
- Step 4: "Passwords do not match." shows.
- Nothing is saved and the setup window stays open.

#### TC-AUTH-07 – Valid setup completes

**Requirement:** REQ-AUTH-03 · **Technique:** EP · **Priority:** H · **Result:** PASS

**Steps**

1. In the setup window enter the correct **Current password**, a valid **New email** on a non-reserved domain, and `Lab-Pinpoint-2026!` in both password boxes.
2. Press **Complete setup**, then **Continue** when "Setup saved" shows.
3. Sign out and sign in with the new email and password.
4. Sign out and try the old bootstrap email and password.

**Expected result**

- Setup saves and the Dashboard opens.
- The new email and password work.
- The old bootstrap login is refused.

#### TC-AUTH-08 – Forced password change

**Requirement:** REQ-AUTH-04 · **Technique:** ST · **Priority:** H · **Result:** PASS

**Before you start:** a user created with **Require password change at first sign-in** ticked (TC-ACC-03). You know the temporary password.

**Steps**

1. Sign in as that user with the temporary password.
2. Read the window **Change your password**. Try to open `/dashboard` in the address bar.
3. Fill **Current (temporary) password**, **New password**, and **Confirm new password** with a compliant new password. Press **Change password**.
4. Sign out and sign in with the new password.
5. Repeat from step 1 on another account, but type the temporary password as the new password.

**Expected result**

- The window blocks every page until the password is changed.
- After the change the app opens normally and the new password works.
- Reusing the current password is refused ("Choose a password different from your current one.").

#### TC-AUTH-09 – Sign out asks for confirmation

**Requirement:** REQ-AUTH-05 · **Technique:** ST · **Priority:** M · **Result:** PASS

**Steps**

1. Signed in, press **Sign Out** at the bottom of the sidebar. The dialog "Sign out of PinPoint?" appears.
2. Press **Cancel**.
3. Press **Sign Out** again and confirm.
4. Type `/dashboard` in the address bar.

**Expected result**

- Cancel keeps you signed in.
- Confirming signs you out.
- `/dashboard` now redirects to `/login`.

#### TC-AUTH-10 – Idle session timeout

**Requirement:** REQ-AUTH-06 · **Technique:** BVA · **Priority:** M · **Result:** PASS

**Before you start:** the shortest session timeout is 15 minutes.

**Steps**

1. As Super Admin open **Settings**, tab **Security**. Set **Session Timeout** to **15 minutes** and press **Save Changes**.
2. Click around for a moment, then leave the tab alone (no clicks, no typing) for 16 minutes.
3. Click any sidebar link.
4. Set **Session Timeout** back to its previous value.

**Expected result**

- The session ends and you land on `/login`.
- The login page shows "Your session expired due to inactivity. Please log in again."
- Any click made before the 15 minutes pass starts the timer again.

#### TC-AUTH-11 – Forgot Password request

**Requirement:** REQ-AUTH-07 · **Technique:** EP · **Priority:** M · **Result:** PASS

**Steps**

1. On `/login` press **Forgot Password?**. The dialog "Forgot your password?" opens.
2. Type a registered user's email and submit.
3. Sign in as Super Admin. A request alert shows in the header bell. Open **Manage Accounts** and find the **Password reset requests** panel.

**Expected result**

- The dialog says "An administrator has been notified."
- The request is listed with **Reset password** (temporary password and confirmation) and **Dismiss**.
- Note: the repository's status file still says this button has no handler. The PASS recorded here means that file is out of date.

#### TC-AUTH-12 – Routes redirect to login

**Requirement:** REQ-AUTH-08 · **Technique:** EG · **Priority:** M · **Result:** PASS

**Steps**

1. Sign out.
2. Type `/`, then `/dashboard`, then `/no-such-page` in the address bar.

**Expected result**

- All three end on `/login`.

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
| TC-ACC-08 | "Send this user email alerts" depends on permission | ACC-07 | DT | L | PASS |
| TC-ACC-09 | The accounts page needs permission | ACC-08 | DT | H | PASS |
| TC-ACC-10 | Add User uses the default role (issue #191) | ACC-09 | EG | M | PASS   |

#### TC-ACC-01 – Add an account

**Requirement:** REQ-ACC-01 · **Technique:** EP · **Priority:** H · **Result:** PASS

**Steps**

1. As Super Admin open **Manage Accounts** and press **+ Add User**.
2. Fill **First Name** `QA`, **Last Name** `Staff`, **Email** `qa.staff@mail-lab.com`.
3. Choose **Role** Staff and **Status** Active. Type `Lab-Pinpoint-2026!` in the password and confirmation boxes.
4. Press the save button.
5. Open **System Logs**, tab **Activity Log**.

**Expected result**

- The dialog closes and the user appears in the table with role Staff and status Active.
- The Activity Log has an entry for creating that account.

#### TC-ACC-02 – Duplicate and invalid emails are refused

**Requirement:** REQ-ACC-01 · **Technique:** EP · **Priority:** M · **Result:** PASS

**Steps**

1. Press **+ Add User** and fill the form with the email of an existing user.
2. Save. Read the message.
3. Change the email to `not-an-email` and save again.

**Expected result**

- The first save is refused ("Email already exists.").
- The second is refused ("Not a valid email.").
- The dialog stays open with what you typed, and no row is added.

#### TC-ACC-03 – "Require password change at first sign-in"

**Requirement:** REQ-ACC-02 · **Technique:** EG · **Priority:** M · **Result:** PASS

**Steps**

1. Press **+ Add User**. Read the checkbox **Require password change at first sign-in**.
2. Create user A with it ticked and user B with it unticked.
3. Sign in as A, then as B (private window).

**Expected result**

- The box is ticked by default.
- User A must change the password before using the app (TC-AUTH-08).
- User B goes straight to the app.

#### TC-ACC-04 – Inactive and suspended users cannot sign in

**Requirement:** REQ-ACC-03 · **Technique:** DT · **Priority:** H · **Result:** PASS

**Steps**

1. Open the Staff user's **Edit Account** dialog. Set **Status** to Inactive and save. Try to sign in as that user.
2. Set the status to Suspended and save. Try to sign in.
3. Set it back to Active and save. Try to sign in.

**Expected result**

- Sign-in is refused while Inactive and while Suspended.
- It works when Active.

#### TC-ACC-05 – Editing a signed-in user signs them out

**Requirement:** REQ-ACC-04 · **Technique:** ST · **Priority:** M · **Result:** FAIL - the suspended account successfully signed out but it didn't have any warning when user session is timed out

**Steps**

1. In a private window sign in as the Staff user and keep the page open.
2. As Super Admin open that user's **Edit Account** dialog. Read the line at the bottom of the dialog.
3. Change the **Role** or **Status** and press **Save Changes**.
4. In the private window click any page.

**Expected result**

- The dialog says "The user will be signed out after changes are applied."
- The user's session ends on its next request and the page goes to `/login`.
- Note: the spec does not ask for a message to the user who is signed out. If the login page shows nothing, record it as an observation, not as a failed sign-out.

#### TC-ACC-06 – Administrator resets another user's password

**Requirement:** REQ-ACC-05 · **Technique:** ST · **Priority:** H · **Result:** FAIL - the administrator cannot change or reset the other user password

**Steps**

1. Open the Staff user's **Edit Account** dialog.
2. Type `Lab-Pinpoint-2027!` in **NEW PASSWORD** and again in **CONFIRM PASSWORD**. If **Save Changes** stays disabled, read the hint under the field: with the strong policy on it needs 12 or more characters with upper and lower case, a number, and a symbol; otherwise 8 or more.
3. Press **Save Changes**.
4. In a private window try the old password, then the new one.

**Expected result**

- The old password no longer works.
- The new password works and the user must change it at once (TC-AUTH-08).
- Note: the code on `main` does include these fields in the edit dialog. If the button stays disabled for a password that meets the policy, or the save fails, write down the exact message and open a defect.

#### TC-ACC-07 – The first (bootstrap) account is protected

**Requirement:** REQ-ACC-06 · **Technique:** DT · **Priority:** H · **Result:** PASS

**Steps**

1. Open **Edit Account** for the first account (the Super Admin created at install).
2. Look at **Status** and at the **Role** list.

**Expected result**

- **Status** is disabled and the dialog says the super admin account cannot be suspended or made inactive.
- Roles that cannot manage accounts and roles are disabled, with the explanation that the bootstrap administrator must keep a role that can manage them.

#### TC-ACC-08 – "Send this user email alerts" depends on permission

**Requirement:** REQ-ACC-07 · **Technique:** DT · **Priority:** L · **Result:** PASS

**Before you start:** a role `qa-accounts` with `account.view` and `account.edit` but not `account.alerts`, and a user with that role.

**Steps**

1. As Super Admin press **+ Add User** and look for the checkbox **Send this user email alerts**. Look at the **Email Alerts** column in the table.
2. Sign in as the `qa-accounts` user, open **Manage Accounts**, and press **+ Add User**.

**Expected result**

- Super Admin sees the checkbox and the column shows On or Off per user.
- The `qa-accounts` user does not see the checkbox.

#### TC-ACC-09 – The accounts page needs permission

**Requirement:** REQ-ACC-08 · **Technique:** DT · **Priority:** H · **Result:** PASS

**Steps**

1. Sign in as the Staff user.
2. Type `/accounts` in the address bar.
3. Open `/api/user/accounts` in the address bar.

**Expected result**

- **Manage Accounts** is not in the sidebar, and `/accounts` redirects to Settings.
- The API returns 403.

#### TC-ACC-10 – Add User uses the default role (issue #191)

**Requirement:** REQ-ACC-09 · **Technique:** EG · **Priority:** M · **Result:** PASS

**Steps**

1. Reload **Manage Accounts** and press **+ Add User** as quickly as you can, before the page finishes loading.
2. Read the **Role** field. Fill the names, a new email, and matching compliant passwords.
3. Press save. Without reloading, press **+ Add User** again and create a second account.
4. Reload the page.

**Expected result**

- The first active role is already selected in **Role**, and **Save** is enabled once the form is valid.
- Both accounts are created and appear in the list without a reload. They are still there after a reload.
- If there are no active roles, **Save** stays disabled and the dialog says to wait for loading or to check the active roles.

### Module 3 – Manage Roles (`/manage-roles`)

**Summary of cases**

| TC | Case | Req | Tech | Pri | Result |
| --- | --- | --- | --- | --- | --- |
| TC-ROL-01 | Create a role | ROL-01 | EP | H | PASS |
| TC-ROL-02 | The Super Admin role is read-only | ROL-02 | EG | M | PASS |
| TC-ROL-03 | The bootstrap administrator's role is locked | ROL-03 | DT | H | PASS |
| TC-ROL-04 | A dashboard-only user is limited to the Dashboard | ROL-04 | DT | H | PASS |
| TC-ROL-05 | A Staff user can open only Settings | ROL-04 | DT | H | PASS |
| TC-ROL-06 | Settings tabs follow their own permissions | ROL-05 | DT | M | PASS |

#### TC-ROL-01 – Create a role

**Requirement:** REQ-ROL-01 · **Technique:** EP · **Priority:** H · **Result:** PASS

**Steps**

1. As Super Admin open **Manage Roles** and press **+ Add Role**.
2. Type **Role Name** `qa-view`, a short description, and tick only the permission `system.dashboard`.
3. Save.
4. Open **System Logs**, tab **Activity Log**.

**Expected result**

- The role shows as Active with exactly that one permission.
- The Activity Log records the creation.

#### TC-ROL-02 – The Super Admin role is read-only

**Requirement:** REQ-ROL-02 · **Technique:** EG · **Priority:** M · **Result:** PASS

**Steps**

1. Open the built-in **Super Admin** role.
2. Try to untick a permission. Try to edit **Role Name**.

**Expected result**

- Every permission is ticked and read-only, with the explanation "The built-in Super Admin role has fixed permissions."
- The role name cannot be edited.

#### TC-ROL-03 – The bootstrap administrator's role is locked

**Requirement:** REQ-ROL-03 · **Technique:** DT · **Priority:** H · **Result:** PASS

**Steps**

1. Open the role assigned to the first (bootstrap) account.
2. Look at the permission checkboxes and at the **Role status** control.
3. Try to make the role Inactive.

**Expected result**

- The role is marked as locked.
- The seven account and role administration permissions are disabled ("Required for the bootstrap administrator to manage accounts and roles.").
- Deactivation is blocked ("This role belongs to the super admin and cannot be deactivated.").

#### TC-ROL-04 – A dashboard-only user is limited to the Dashboard

**Requirement:** REQ-ROL-04 · **Technique:** DT · **Priority:** H · **Result:** PASS

**Before you start:** the role `qa-view` (TC-ROL-01) and a user with that role, for example `qa.view@mail-lab.com`.

**Steps**

1. Sign in as that user and read the sidebar.
2. Type each of these addresses one at a time: `/network-health`, `/device-inventory`, `/topology`, `/system-status`, `/plugins`, `/ncpa-deployment`, `/maintenance`, `/remediation`, `/history`, `/reports`, `/system-logs`, `/accounts`, `/manage-roles`.
3. Open these API addresses in the address bar: `/api/system/log`, `/api/system/report/availability`, `/api/user/accounts`.

**Expected result**

- The sidebar shows **Overview** (and **Settings**) only.
- Every address in step 2 redirects back to the Dashboard.
- Every API address in step 3 returns 403.

#### TC-ROL-05 – A Staff user can open only Settings

**Requirement:** REQ-ROL-04 · **Technique:** DT · **Priority:** H · **Result:** PASS

**Steps**

1. Sign in as the Staff user.
2. Read the sidebar and the tabs in **Settings**.
3. Type `/dashboard` in the address bar.

**Expected result**

- After signing in the user lands on **Settings**. The sidebar shows only Settings.
- Only the **General Settings** tab shows.
- `/dashboard` redirects back to Settings.

#### TC-ROL-06 – Settings tabs follow their own permissions

**Requirement:** REQ-ROL-05 · **Technique:** DT · **Priority:** M · **Result:** PASS

**Before you start:** a role `qa-sec` with only `settings.security` and a user with that role.

**Steps**

1. Sign in as that user and open **Settings**.
2. Read the tab list.

**Expected result**

- Only **General Settings** and **Security** show.
- **System**, **Network Discovery**, **Plugins**, and **Email** are not offered.

## Test cases: monitoring views

### Module 4 – Dashboard (sidebar: Overview, `/dashboard`)

**Summary of cases**

| TC | Case | Req | Tech | Pri | Result |
| --- | --- | --- | --- | --- | --- |
| TC-DASH-01 | The four summary cards | DASH-01 | EP | H | PASS |
| TC-DASH-02 | A paused device is left out of the counts | DASH-02 | ST | H | PASS |
| TC-DASH-03 | The Active Alerts table matches the cards | DASH-03 | DT | H | PASS |
| TC-DASH-04 | All-clear state | DASH-03 | EG | M | PASS |
| TC-DASH-05 | Service Overview panel | DASH-04 | EP | M | PASS |
| TC-DASH-06 | Refresh text and stale Nagios warning | DASH-05 | BVA | M | FAIL - While Nagios is down, there is no indication that Nagios is not running and not polling, this was confirmed when trying to modify a Nagios config but can't save. |
| TC-DASH-07 | "No data" instead of blank cards | DASH-06 | EG | M | PASS |
| TC-DASH-08 | The Dashboard needs permission | DASH-07 | DT | H | PASS |
| TC-DASH-09 | "Running out soon" forecast list (issue #156) | DASH-08 | EP | M | PASS |

The page has: the header with the refresh text and the **Rescan Network** button, the **Appliance storage** card, four cards (**Total Hosts**, **Network Latency**, **Active Warnings**, **Critical Issues**), **Network Status Overview** (Online and Offline), **Network Performance**, **Average Resource Utilization** (only when an NCPA host reports), **Running out soon**, the **Active Alerts** table, **Recent Notifications**, and the **Service Overview** panel on the right.

#### TC-DASH-01 – The four summary cards

**Requirement:** REQ-DASH-01 · **Technique:** EP · **Priority:** H · **Result:** PASS (re-check: this case was reworded to match the real cards)

**Before you start:** the lab has hosts Up and Down and at least one Warning and one Critical service.

**Steps**

1. Open **Overview**.
2. Read **Total Hosts** and its line "N online".
3. Read **Network Latency** (milliseconds) and its line ("N% packet loss", or "No data").
4. Read **Active Warnings** (line "Needs attention") and **Critical Issues** (line "N hosts down", or "Immediate action").
5. Open **Device Inventory** (default **Monitored** filter) and count the hosts. Count the rows in the **Active Alerts** table by state.

**Expected result**

- **Total Hosts** equals the number of monitored hosts, and "N online" equals the hosts that are Up.
- **Active Warnings** equals the warning-level alerts and **Critical Issues** equals the critical ones in the **Active Alerts** table.
- **Network Latency** shows a number with packet loss, or "No data" when no ping check exists.
- Note: the spec describes cards for Total Services, Active Alerts, and Hosts in Downtime. The app shows the four above. Service totals are in **Service Overview**. Report this as a spec gap, not a defect.

#### TC-DASH-02 – A paused device is left out of the counts

**Requirement:** REQ-DASH-02 · **Technique:** ST · **Priority:** H · **Result:** PASS

**Steps**

1. On **Overview** write down **Total Hosts**, **Active Warnings**, and **Critical Issues**.
2. In **Device Inventory** open a monitored host (**View host details**), find **Monitoring**, press **Pause monitoring**, and confirm.
3. Reload **Overview**.
4. Go back and press **Resume monitoring**, confirm, wait one polling interval, and reload **Overview**.

**Expected result**

- While paused, the host and its services are not counted and do not appear in **Active Alerts** or **Service Overview**.
- After resuming, the numbers return to step 1.

#### TC-DASH-03 – The Active Alerts table matches the cards

**Requirement:** REQ-DASH-03 · **Technique:** DT · **Priority:** H · **Result:** PASS

**Steps**

1. Make one host Down (stop the web VM from the hypervisor) and one service Critical (stop its service on the other VM). Wait for the next check.
2. Open **Overview** and read the **Active Alerts** table (columns: Affected Device/Service, Status, Since, Output, Actions).
3. Compare the table with **Active Warnings** and **Critical Issues**.

**Expected result**

- Every host that is not Up and every service that is not OK is listed once.
- The counts on the cards agree with the table.

#### TC-DASH-04 – All-clear state

**Requirement:** REQ-DASH-03 · **Technique:** EG · **Priority:** M · **Result:** PASS (re-check: wording changed)

**Steps**

1. Restore every host and service so all are Up and OK. Wait for the next check.
2. Open **Overview**.

**Expected result**

- **Active Warnings** and **Critical Issues** show 0.
- The **Active Alerts** table says "No active alerts" and **Service Overview** says "All services OK". No blank area is left.

#### TC-DASH-05 – Service Overview panel

**Requirement:** REQ-DASH-04 · **Technique:** EP · **Priority:** M · **Result:** PASS

**Steps**

1. With one Critical, one Warning, and one Unknown service, open **Overview**.
2. Read the **Service Overview** panel on the right.

**Expected result**

- Counts for Critical, Warning, and Unknown match **System Status**.
- Flapping and scheduled downtime appear when they apply, and a message shows when Nagios is not checking.

#### TC-DASH-06 – Refresh text and stale Nagios warning

**Requirement:** REQ-DASH-05 · **Technique:** BVA · **Priority:** M · **Result:** FAIL

**Steps**

1. In **Settings**, **General Settings**, set **Dashboard Refresh Rate** to **Auto Refresh - 1 minute** and save. Open **Overview** and read the header line.
2. Set it to **Manual** and save. Read the header line again.
3. On the appliance stop Nagios (`systemctl stop nagios`). Wait a few minutes and reload **Overview**.
4. Start Nagios again.

**Expected result**

- The header reads "Auto-refreshing every 1 min", then "Auto-refresh: Manual".
- While Nagios is stopped, **Service Overview** warns that Nagios is not checking hosts and services, so their states will not change. Write down the exact wording you see.

#### TC-DASH-07 – "No data" instead of blank cards

**Requirement:** REQ-DASH-06 · **Technique:** EG · **Priority:** M · **Result:** PASS

**Before you start:** a lab with no ping check on any host and no NCPA host.

**Steps**

1. Open **Overview**.
2. Read **Network Latency**, **Network Performance**, and look for **Average Resource Utilization**.

**Expected result**

- **Network Latency** and **Network Performance** show "No data", not an empty box.
- **Average Resource Utilization** is not shown at all.

#### TC-DASH-08 – The Dashboard needs permission

**Requirement:** REQ-DASH-07 · **Technique:** DT · **Priority:** H · **Result:** PASS

**Steps**

1. Sign in as the Staff user.
2. Type `/dashboard` in the address bar.

**Expected result**

- **Overview** is not in the sidebar and `/dashboard` redirects to Settings.

#### TC-DASH-09 – "Running out soon" forecast list (issue #156)

**Requirement:** REQ-DASH-08 · **Technique:** EP · **Priority:** M · **Result:** PASS

**Before you start:** an NCPA host with at least 3 days of disk or memory readings, and one disk or memory value that is rising. The forecast job runs every 30 minutes.

**Steps**

1. Open **Overview** and find **Running out soon**.
2. Read each row: the metric, the device, the estimated date, "in about N days", and its basis such as "based on the last 3 days".
3. Press **How is this calculated?** and read the note.
4. Repeat on a lab with a new NCPA host that has less than 3 days of data.
5. Repeat on a lab where nothing is rising.

**Expected result**

- Rows are listed with the soonest date first.
- A new host shows a "not enough data yet" message instead of a date.
- When nothing is on course the list says "Nothing is on course to reach a threshold."
- While loading it says "Loading forecasts…".
- The forecast is a display only and changes nothing in Nagios.

### Module 5 – Network Health (`/network-health`) and the host table

**Summary of cases**

| TC | Case | Req | Tech | Pri | Result |
| --- | --- | --- | --- | --- | --- |
| TC-NH-01 | Overview cards | NH-01 | EP | M | PASS |
| TC-NH-02 | Host table search and filters (Device Inventory) | NH-02 | EP | H | PASS |
| TC-NH-03 | Host paging limits (API) | NH-03 | BVA | M | PASS |
| TC-NH-04 | Host detail drawer (Device Inventory) | NH-04 | EP | M | PASS |
| TC-NH-05 | Averages need enough data | NH-05 | BVA | M | PASS |
| TC-NH-06 | Interface Bandwidth | NH-06 | EP | M | PASS |
| TC-NH-07 | Flap history and "Flapping only" (Device Inventory) | NH-07 | BVA | L | PASS |

The Network Health page shows: **Online Devices**, **Offline Devices**, host availability, system activity, **Interface Bandwidth**, CPU load, added plugins, **Latency**, **Packets Loss**, **Bandwidth**, **Avg. Response Time**, active connections, and insights. The host table, its search and filters, and the host drawer are on the **Device Inventory** page. The spec places them under Network Health, so TC-NH-02 to TC-NH-04 and TC-NH-07 are done on Device Inventory.

#### TC-NH-01 – Overview cards

**Requirement:** REQ-NH-01 · **Technique:** EP · **Priority:** M · **Result:** PASS

**Steps**

1. Open **Network Health**.
2. Read **Online Devices** and **Offline Devices**.
3. Open **Overview** and compare with **Total Hosts** and "N online".

**Expected result**

- The online and offline counts agree with the Dashboard.
- Cards with no data show "No data" or a not-configured message, never a blank box.

#### TC-NH-02 – Host table search and filters (Device Inventory)

**Requirement:** REQ-NH-02 · **Technique:** EP · **Priority:** H · **Result:** PASS

**Steps**

1. Open **Device Inventory**.
2. In **Search hostname** type part of a host name.
3. Clear it. Open **Filter** and choose the state Down, then an acknowledgement option, then a **Monitoring** option.
4. Press **Sort** and change the order.

**Expected result**

- A partial name matches. Each filter returns only matching hosts.
- Columns show Hostname, IP Address, State, Latency, Last Check, Monitoring, Flags, Acknowledgement, and Actions.

#### TC-NH-03 – Host paging limits (API)

**Requirement:** REQ-NH-03 · **Technique:** BVA · **Priority:** M · **Result:** PASS

**Steps**

1. While signed in, open these addresses one at a time: `/api/system/network-health/hosts?per_page=0`, `?per_page=1`, `?per_page=100`, `?per_page=101`, and `/api/system/network-health/hosts` with no `per_page`.
2. Count the items returned.

**Expected result**

- 1 and 100 are accepted and return up to that many hosts.
- 0 and 101 are refused (400) or limited, as the API documents (allowed range 1 to 100).
- With no `per_page` the page holds 25 hosts.

#### TC-NH-04 – Host detail drawer (Device Inventory)

**Requirement:** REQ-NH-04 · **Technique:** EP · **Priority:** M · **Result:** PASS

**Steps**

1. On **Device Inventory** press **View host details** on a host row.
2. Read the drawer.

**Expected result**

- The drawer opens without leaving the page.
- It shows **Performance data** (with warning and critical values), **Timestamps** (last check, last up, last down, and so on), and the **Services** on that host.

#### TC-NH-05 – Averages need enough data

**Requirement:** REQ-NH-05 · **Technique:** BVA · **Priority:** M · **Result:** PASS

**Steps**

1. On a lab where only one host has a ping check, read **Latency** and **Packets Loss** on **Network Health**.
2. Add a ping check on a second host, wait for new data, and read them again.

**Expected result**

- With one reporting host the page does not present a single-host number as a network average. Write down exactly what it shows (for example "No data" or "Insufficient data").
- With two or more hosts a network-wide average appears.

#### TC-NH-06 – Interface Bandwidth

**Requirement:** REQ-NH-06 · **Technique:** EP · **Priority:** M · **Result:** PASS

**Before you start:** a device with SNMP whose interface is monitored (TC-DX-07).

**Steps**

1. On **Network Health** find **Interface Bandwidth**.
2. Choose a device, then an interface.
3. Choose each time range, from 1 hour to 7 days.
4. Choose a device that has no monitored interface.

**Expected result**

- Inbound and outbound lines draw, and the unit scales (Kbit/s, Mbit/s, and so on) with the traffic.
- Messages show for no device, no interface, no data, or too little data.
- A failure in this card does not blank the rest of the page.

#### TC-NH-07 – Flap history and "Flapping only" (Device Inventory)

**Requirement:** REQ-NH-07 · **Technique:** BVA · **Priority:** L · **Result:** PASS

**Steps**

1. On **Device Inventory** press **View host details** on a host. Find **Flap history**.
2. In **Flap history window** choose **Last hour**, **Last 6 hours**, **Last 24 hours**, and **Last 7 days**.
3. Back in the host table open **Filter** and tick **Flapping only**.

**Expected result**

- Each window shows how many times the host flapped in that period, or "Not flagged as flapping in this period."
- **Flapping only** lists only flapping hosts.
- If Nagios flap detection is off, a warning says so.

### Module 6 – System Status (`/system-status`)

**Summary of cases**

| TC | Case | Req | Tech | Pri | Result |
| --- | --- | --- | --- | --- | --- |
| TC-SS-01 | Service state counts | SS-01 | EP | H | PASS |
| TC-SS-02 | Search, filter, sort, and paging | SS-01 | EP | M | PASS |
| TC-SS-03 | No results | SS-01 | EG | L | PASS |
| TC-SS-04 | System Status needs permission | SS-02 | DT | H | PASS |
| TC-SS-05 | Forecast badge on a service row (issue #156) | SS-03 | EP | M | PASS |

#### TC-SS-01 – Service state counts

**Requirement:** REQ-SS-01 · **Technique:** EP · **Priority:** H · **Result:** PASS

**Steps**

1. Open **System Status**.
2. Read the summary (needs attention, running normally, and the Critical, Warning, and Unknown counts).
3. Count the rows in the service table.

**Expected result**

- The counts add up to the number of services in the table, and agree with **Service Overview** on the Dashboard.

#### TC-SS-02 – Search, filter, sort, and paging

**Requirement:** REQ-SS-01 · **Technique:** EP · **Priority:** M · **Result:** PASS

**Steps**

1. In **Search host or service** type part of a service name.
2. Clear it, open **Filter**, and choose Critical.
3. Click a column title to sort.
4. Go to the next page.

**Expected result**

- The search narrows the list, the filter keeps only Critical rows, sorting reorders them, and paging keeps the filter.

#### TC-SS-03 – No results

**Requirement:** REQ-SS-01 · **Technique:** EG · **Priority:** L · **Result:** PASS

**Steps**

1. In **Search host or service** type text that matches nothing, such as `zzzzzz`.

**Expected result**

- The table says "No services match your search or filter", not an error or a blank page.

#### TC-SS-04 – System Status needs permission

**Requirement:** REQ-SS-02 · **Technique:** DT · **Priority:** H · **Result:** PASS

**Steps**

1. Sign in as the Staff user.
2. Type `/system-status` in the address bar.

**Expected result**

- **System Status** is not in the sidebar and the address redirects to Settings.

#### TC-SS-05 – Forecast badge on a service row (issue #156)

**Requirement:** REQ-SS-03 · **Technique:** EP · **Priority:** M · **Result:** PASS

**Before you start:** the same lab as TC-DASH-09.

**Steps**

1. Open **System Status** and find the disk or memory service of the NCPA host.
2. Read the badge on the row and hover over it.
3. Find the same kind of service on a host with little data.

**Expected result**

- A rising metric shows a badge such as "Estimate: warning level in about 6 days". The tooltip names the metric and its basis.
- A host with little data shows "Not enough data yet".

### Module 7 – Alert acknowledgement

**Summary of cases**

| TC | Case | Req | Tech | Pri | Result |
| --- | --- | --- | --- | --- | --- |
| TC-ACK-01 | Acknowledge needs a comment | ACK-02 | EP | H | PASS |
| TC-ACK-02 | No acknowledge without permission | ACK-01 | DT | H | PASS |
| TC-ACK-03 | Acknowledge all | ACK-03 | EP | H | PASS |
| TC-ACK-04 | Acknowledge all counts only unacknowledged alerts | ACK-03 | DT | M | PASS |
| TC-ACK-05 | Unacknowledge | ACK-04 | ST | H | FAIL - see details in step-by-step |
| TC-ACK-06 | Acknowledgement filters | ACK-05 | DT | M | FAIL - See note |
| TC-ACK-07 | Acknowledged alerts sort below others | ACK-06 | EG | L | PASS |
| TC-ACK-08 | Acknowledgement clears on recovery | ACK-07 | ST | H | PASS |

Acknowledge buttons are on the **Active Alerts** table (Dashboard), the host rows and drawer (**Device Inventory**), and the service rows (**System Status**). A comment is required.

#### TC-ACK-01 – Acknowledge needs a comment

**Requirement:** REQ-ACK-02 · **Technique:** EP · **Priority:** H · **Result:** PASS

**Steps**

1. On **Overview**, in the **Active Alerts** table, press **Acknowledge** on one alert.
2. Leave "Add a comment explaining the acknowledgement." empty and look at the confirm button.
3. Type `Investigating` and confirm.

**Expected result**

- With an empty comment the confirm button is disabled.
- With a comment the row changes to acknowledged and shows who did it. The button becomes **Unacknowledge**.

#### TC-ACK-02 – No acknowledge without permission

**Requirement:** REQ-ACK-01 · **Technique:** DT · **Priority:** H · **Result:** PASS

**Before you start:** the dashboard-only user (role `qa-view`, which lacks `system.acknowledge_alerts`) and an active alert.

**Steps**

1. Sign in as the dashboard-only user and open **Overview**.
2. Look at the **Active Alerts** table and its **Actions** column.

**Expected result**

- The alerts are visible, and acknowledged ones show as acknowledged.
- No **Acknowledge** or **Unacknowledge** control is shown.

#### TC-ACK-03 – Acknowledge all

**Requirement:** REQ-ACK-03 · **Technique:** EP · **Priority:** H · **Result:** PASS

**Steps**

1. With 3 unacknowledged alerts, find the button "Acknowledge 3 active alerts" above the table.
2. Press it, type one comment, and confirm.

**Expected result**

- The dialog is titled "Acknowledge 3 active alerts" and asks for one comment.
- All 3 alerts become acknowledged with that same comment and your name.

#### TC-ACK-04 – Acknowledge all counts only unacknowledged alerts

**Requirement:** REQ-ACK-03 · **Technique:** DT · **Priority:** M · **Result:** PASS

**Steps**

1. With 3 unacknowledged alerts, acknowledge one alert on its own.
2. Read the all-alerts button.
3. Press it and confirm with a comment.

**Expected result**

- The button now says "Acknowledge 2 active alerts".
- After confirming, all 3 alerts are acknowledged, and the first alert keeps its original comment.
- Note: the spec describes acknowledging "visible" alerts after a filter. The Dashboard has no filter (see TC-ACK-06).

#### TC-ACK-05 – Unacknowledge

**Requirement:** REQ-ACK-04 · **Technique:** ST · **Priority:** H · **Result:** FAIL - there is no prompt to ask you if you want to remove the acknowledge for the alert

**Steps**

1. On an acknowledged alert press **Unacknowledge**.
2. Look for a confirmation question.
3. Open **Device Inventory** or **System Status** and check the same item.

**Expected result**

- The acknowledgement is removed on every page and the button returns to **Acknowledge**. No comment is needed.
- Note (spec gap): the spec says to ask "Remove acknowledgement for this alert?" first. The app removes it at once. Keep this as a finding.

#### TC-ACK-06 – Acknowledgement filters

**Requirement:** REQ-ACK-05 · **Technique:** DT · **Priority:** M · **Result:** There is no filter in acknowledgement/ active alerts

**Steps**

1. On **Overview** look for an acknowledgement filter on the **Active Alerts** table.
2. On **Device Inventory** and **System Status** open **Filter** and look for acknowledgement options.
3. On **History**, tab **Alerts**, open the **Acknowledged** filter and choose **Acknowledged only**, then **Unacknowledged only**.

**Expected result**

- The Dashboard table has no filter (spec gap: the spec asks for Show all, Hide acknowledged, Show only acknowledged).
- Where a filter exists, it returns only matching rows.

#### TC-ACK-07 – Acknowledged alerts sort below others

**Requirement:** REQ-ACK-06 · **Technique:** EG · **Priority:** L · **Result:** PASS

**Steps**

1. Have one acknowledged and one unacknowledged alert of the same severity.
2. Read the order in the **Active Alerts** table.

**Expected result**

- The acknowledged one is below the unacknowledged one, shown muted with who acknowledged it.

#### TC-ACK-08 – Acknowledgement clears on recovery

**Requirement:** REQ-ACK-07 · **Technique:** ST · **Priority:** H · **Result:** PASS

**Steps**

1. Acknowledge a Down host or Critical service.
2. Fix the target and wait for Up or OK.
3. Open **History**, tab **Alerts**.
4. Break the target again.

**Expected result**

- After recovery the acknowledgement is gone and History has an automatic resolved record with no user.
- The new problem starts unacknowledged.
- Note: the status file says this was tested only in isolation, not yet in a live lab. A failure here may be a real finding.

### Module 8 – History (`/history`)

**Summary of cases**

| TC | Case | Req | Tech | Pri | Result |
| --- | --- | --- | --- | --- | --- |
| TC-HIS-01 | History needs permission | HIS-01 | DT | H | PASS |
| TC-HIS-02 | Time presets | HIS-02 | EP | M | PASS |
| TC-HIS-03 | Filters work together | HIS-02 | DT | M | PASS |
| TC-HIS-04 | Date range rules (API) | HIS-03 | BVA | M | PASS |
| TC-HIS-05 | Sorting | HIS-04 | EP | L | PASS |
| TC-HIS-06 | Rows per page | HIS-05 | BVA | L | PASS |
| TC-HIS-07 | Row detail and the link between tabs | HIS-06 | EP | M | PASS |
| TC-HIS-08 | Filters with no results | HIS-02 | EG | L | PASS |

The page has two tabs, **Alerts** and **Notifications**. Filters: **Time range**, **Type**, **Host**, **Service**, **New state**, **Acknowledged**, **State type**, **Source** (notifications), **Apply**, **Clear filters**, and **Rows per page**.

#### TC-HIS-01 – History needs permission

**Requirement:** REQ-HIS-01 · **Technique:** DT · **Priority:** H · **Result:** PASS

**Steps**

1. Sign in as the Staff user.
2. Type `/history` in the address bar. Open `/api/system/history/alerts`.

**Expected result**

- **History** is not in the sidebar, the address redirects away, and the API returns 403.

#### TC-HIS-02 – Time presets

**Requirement:** REQ-HIS-02 · **Technique:** EP · **Priority:** M · **Result:** PASS

**Steps**

1. Open **History**, tab **Alerts**. Read the default **Time range**.
2. Choose **Last hour**, **Last 6 hours**, **Last 24 hours**, **Last 7 days**, and **Last 30 days**, checking the **Time** column each time.

**Expected result**

- The default is **Last 24 hours**.
- Each preset shows only events inside that period.

#### TC-HIS-03 – Filters work together

**Requirement:** REQ-HIS-02 · **Technique:** DT · **Priority:** M · **Result:** PASS

**Steps**

1. Set **Type** to **Service only**, **New state** to Critical, **State type** to **Hard only**, and **Acknowledged** to **Acknowledged only**.
2. Press **Apply**.
3. Press **Clear filters**.

**Expected result**

- Every row matches all four filters.
- **Clear filters** returns the full list.

#### TC-HIS-04 – Date range rules (API)

**Requirement:** REQ-HIS-03 · **Technique:** BVA · **Priority:** M · **Result:** PASS

**Steps**

1. Open `/api/system/history/alerts?start_date=2026-10-01&end_date=2026-10-02`.
2. Open it with only `start_date`.
3. Open it with `start_date=2026-10-02&end_date=2026-10-01` (reversed).
4. Open it with `start_date=abc&end_date=def`.

**Expected result**

- Step 1 returns events (or an empty list).
- Steps 2, 3, and 4 are refused with an error and no data.
- With no dates and no preset the range is the past 24 hours.

#### TC-HIS-05 – Sorting

**Requirement:** REQ-HIS-04 · **Technique:** EP · **Priority:** L · **Result:** PASS

**Steps**

1. Open **History** and read the order of the **Time** column.
2. Click the **Host** column title, then **New state**.

**Expected result**

- The default is newest first. Each column sorts, with newest first as the tie-break.

#### TC-HIS-06 – Rows per page

**Requirement:** REQ-HIS-05 · **Technique:** BVA · **Priority:** L · **Result:** PASS

**Steps**

1. Set **Rows per page** to 25, then 50, then 100.

**Expected result**

- Each page shows at most that many rows, and the total count shows above the table.

#### TC-HIS-07 – Row detail and the link between tabs

**Requirement:** REQ-HIS-06 · **Technique:** EP · **Priority:** M · **Result:** PASS

**Steps**

1. On **Alerts** expand an alert row that had a notification.
2. Press **Related notifications** or **View notification**.
3. On the **Notifications** tab expand a row and press **View in Alerts History**.
4. Expand an alert that had no notification.

**Expected result**

- The row shows its detail (previous to new state, plugin output, who acknowledged).
- The link switches tabs and opens the matching row.
- An alert with no notification says "No notifications were sent for this alert."

#### TC-HIS-08 – Filters with no results

**Requirement:** REQ-HIS-02 · **Technique:** EG · **Priority:** L · **Result:** PASS

**Steps**

1. Pick a host and **New state** combination that never happened, then press **Apply**.

**Expected result**

- An empty-state message shows ("No matching alert event was found." or similar), not an error.

## Test cases: device modules

### Module 9 – Device Inventory (`/device-inventory`)

**Summary of cases**

| TC | Case | Req | Tech | Pri | Result |
| --- | --- | --- | --- | --- | --- |
| TC-DI-01 | Who sees the Ports section | DI-01 | DT | H | PASS |
| TC-DI-02 | Port groups and their order | DI-02 | EP | M | PASS |
| TC-DI-03 | One reason per port | DI-03 | DT | M | PASS |
| TC-DI-04 | View-only without edit permission | DI-04 | DT | H | PASS |
| TC-DI-05 | Stop and resume monitoring | DI-05, DI-06 | ST | H | PASS |
| TC-DI-06 | Leave suggested holds the port | DI-07 | ST | M | PASS |
| TC-DI-07 | Service name rules in Set service | DI-08 | BVA | H | PASS |
| TC-DI-08 | The "Checked by" line | DI-08 | EP | M | PASS |
| TC-DI-09 | Pin and Remove pin | DI-09 | ST | M | FAIL - Notes in the step-by-step  |
| TC-DI-10 | The NCPA port is protected | DI-10 | EG | M | PASS |
| TC-DI-11 | One monitoring label per device | DI-11 | DT | H | PASS |
| TC-DI-12 | Monitoring filter | DI-11 | EP | M | PASS |
| TC-DI-13 | Pause and resume | DI-12 | ST | H | PASS |
| TC-DI-14 | Invalid pause and resume | DI-12 | DT | M | PASS |
| TC-DI-15 | Out-of-config devices show "last known status" | DI-13 | EG | M | PASS |
| TC-DI-16 | Needs Review section | DI-14 | DT | M | PASS |
| TC-DI-17 | The review drawer writes nothing | DI-14 | EP | M | PASS |
| TC-DI-18 | Merging needs edit permission and two distinct records | DI-14 | DT | H | PASS |
| TC-DI-19 | Merge confirmation | DI-14 | ST | H | PASS |

To open a host's drawer press **View host details** on its row. The drawer has the **Services** list, **Performance data**, **Timestamps**, **Acknowledgement**, and, for a discovered device, sections such as **Monitoring**, **Ports**, **SNMP**, **Interfaces**, **Email alert recipients**, and **Parent devices**. Pressing a service in the list shows the service view, and **Back to host** returns.

**9a. Ports**

#### TC-DI-01 – Who sees the Ports section

**Requirement:** REQ-DI-01 · **Technique:** DT · **Priority:** H · **Result:** PASS

**Steps**

1. As Super Admin open **Device Inventory** and press **View host details** on a discovered host.
2. Scroll the drawer and look for **Ports**.
3. Open the drawer of `localhost` (the Nagios server, which has no device record).
4. Sign in as a user with `system.network_health` but not `system.hosts` and open the same discovered host.

**Expected result**

- A discovered host shows **Ports** for Super Admin.
- `localhost` shows no **Ports** section.
- The user without `system.hosts` does not see **Ports**.

#### TC-DI-02 – Port groups and their order

**Requirement:** REQ-DI-02 · **Technique:** EP · **Priority:** M · **Result:** PASS

**Before you start:** a device with ports in several states (Monitored, Suggested, Ignored, Archived).

**Steps**

1. Open that device's drawer and read the **Ports** groups from top to bottom.
2. Read the count in each group header and the order inside a group.

**Expected result**

- Groups appear in this order: **Needs attention**, **Monitored**, **Suggested**, **Stopped**, **Archived** (collapsed).
- Each header has a count, and a group with no ports is not shown.
- Inside a group, TCP ports come before UDP, each by port number.

#### TC-DI-03 – One reason per port

**Requirement:** REQ-DI-03 · **Technique:** DT · **Priority:** M · **Result:** PASS

**Before you start:** a Suggested port that is both held (**Leave suggested**) and flagged **Not used as intended**.

**Steps**

1. Open the device drawer and find that port in **Ports**.
2. Read the reason text under it.

**Expected result**

- Exactly one reason shows.
- It is "Not used as intended: expected …, found …. Not monitored until acknowledged." (the first matching reason wins), not the "Held back" reason.

#### TC-DI-04 – View-only without edit permission

**Requirement:** REQ-DI-04 · **Technique:** DT · **Priority:** H · **Result:** PASS

**Before you start:** a user whose role has `system.network_health` and `system.hosts` but not `system.hosts.edit`.

**Steps**

1. Sign in as that user and open a discovered device's drawer.
2. Look at **Ports**.

**Expected result**

- No action buttons show on any port.
- The note "You can view ports but not change them." shows once.

#### TC-DI-05 – Stop and resume monitoring

**Requirement:** REQ-DI-05, REQ-DI-06 · **Technique:** ST · **Priority:** H · **Result:** PASS

**Steps**

1. In **Ports** pick a Monitored port and press **Stop monitoring**. Read the question and press **Cancel**.
2. Press **Stop monitoring** again and confirm.
3. Look for the port in the **Stopped** group, then open **System Status** and search the service.
4. Return, press **Resume** on the port.

**Expected result**

- The question names the service and host and says its Nagios service is removed and its history kept.
- Cancel changes nothing.
- After confirming, the port is Ignored (in **Stopped**) and its service leaves **System Status**.
- **Resume** makes the port Monitored again and the service returns.

#### TC-DI-06 – Leave suggested holds the port

**Requirement:** REQ-DI-07 · **Technique:** ST · **Priority:** M · **Result:** PASS

**Steps**

1. On a Monitored port press **Leave suggested** and confirm.
2. Press **Rescan Network** on the Dashboard and wait for it to finish.
3. In **Plugins** disable the port's plugin, then enable it again.
4. Reopen the device's **Ports**.

**Expected result**

- The port becomes Suggested and shows **Held**, and its Nagios service is removed.
- After the rescan and after the plugin is disabled and enabled, it is still Suggested and not monitored.

#### TC-DI-07 – Service name rules in Set service

**Requirement:** REQ-DI-08 · **Technique:** BVA · **Priority:** H · **Result:** PASS

**Steps**

1. On a port press **Set service…**. The dialog is titled "Set service for {protocol}/{port} on {host}".
2. In **Service name** type each of these and watch the **Save** button: `ssh`, `SSH`, `-ssh`, `my_svc-1`, a name of exactly 32 letters, a name of 33 letters, and an empty field.
3. Type `ssh` again for a port that already has the service `ssh`.

**Expected result**

- Valid: `ssh`, `my_svc-1`, and the 32-letter name (lowercase letters, digits, `-`, or `_`, starting with a letter or digit, at most 32).
- Invalid: `SSH`, `-ssh`, the 33-letter name, and the empty field. **Save** stays disabled.
- **Save** is also disabled when the name is unchanged.

#### TC-DI-08 – The "Checked by" line

**Requirement:** REQ-DI-08 · **Technique:** EP · **Priority:** M · **Result:** PASS

**Steps**

1. In **Set service…** on a TCP port type `http`.
2. Type an unknown name such as `myapp` on the same TCP port.
3. Open the dialog on a UDP port and type `myapp`.

**Expected result**

- `http` shows the plugin `check_http`.
- The unknown TCP name shows "check\_tcp (generic TCP check)".
- The unknown UDP name shows "Skipped: no check exists for this UDP service".
- The text "Scans will no longer change this port's service on this device." is always shown.

#### TC-DI-09 – Pin and Remove pin

**Requirement:** REQ-DI-09 · **Technique:** ST · **Priority:** M · **Result:** FAIL - Using network discovery again assigns the device with a port 80 named into a different service name to a new record in network discovery, and saying that the old record has an unknown IP address. The same device is said to have a different SSH key despite being the same device, this needs to be investigated, the device used is 10.77.0.8.

**Steps**

1. On a Monitored `http` port press **Set service…**, type `webapp`, and save. Open **System Status** and look for the service.
2. Return and press **Remove pin**. Read the question and confirm.
3. Look at the port's service name in **System Status**.
4. Press **Rescan Network** once.
5. Try to find **Remove pin** on a port that was never pinned.

**Expected result**

- Step 1: the Nagios service is renamed (the old name's history stays under the old name). The port shows **Pinned**.
- Step 2: the question says the Nagios service is not changed and a later different scan result is recorded for review. The port keeps its service name.
- Step 5: **Remove pin** is not offered. (Calling the API for it returns "This port is not pinned.")

#### TC-DI-10 – The NCPA port is protected

**Requirement:** REQ-DI-10 · **Technique:** EG · **Priority:** M · **Result:** PASS

**Before you start:** a host with a successful NCPA deployment.

**Steps**

1. Open that host's drawer, **Ports**, and find the NCPA port.

**Expected result**

- The row reads "Managed by NCPA deployment".
- It offers no Stop monitoring, Ignore, Leave suggested, Set service, or Remove pin.

**9b. Monitoring state**

#### TC-DI-11 – One monitoring label per device

**Requirement:** REQ-DI-11 · **Technique:** DT · **Priority:** H · **Result:** PASS

**Steps**

1. In the **Monitoring** column look at a normal device, a paused device, a device whose address now belongs to another device, and a missing device.
2. Look at a device that is both paused and missing, and one that is retired and paused.
3. Look at the `localhost` row.

**Expected result**

- The labels are Monitored, Paused, Address unknown, Missing, Retired, or Merged, shown as a chip with a tooltip reason.
- Both-paused-and-missing shows Paused. Retired and paused shows Retired.
- `localhost` has no chip and shows — in the column.

#### TC-DI-12 – Monitoring filter

**Requirement:** REQ-DI-11 · **Technique:** EP · **Priority:** M · **Result:** PASS

**Steps**

1. Open **Device Inventory**. Read which Monitoring option is chosen when the page opens.
2. Open **Filter** and try **All**, **Monitored**, **Not monitored**, and one single label such as **Paused**.
3. Open `/api/system/network-health/hosts?monitoring=nonsense` in the address bar.

**Expected result**

- The page opens on **Monitored**.
- Each option returns the right hosts. **Not monitored** returns every label except Monitored, and **Monitored** includes hosts with no device record.
- The API call returns 400.

#### TC-DI-13 – Pause and resume

**Requirement:** REQ-DI-12 · **Technique:** ST · **Priority:** H · **Result:** PASS

**Steps**

1. In a host drawer find **Monitoring** and press **Pause monitoring**. Read the question.
2. Press **Cancel**, then press **Pause monitoring** again and confirm.
3. Run **Rescan Network** and wait for it to finish.
4. Open **Overview** and check the totals.
5. Return and press **Resume monitoring**, then confirm.
6. Open **System Logs**, tab **Activity Log**.

**Expected result**

- The question says Nagios will stop checking the device and all its services, and scans keep tracking it.
- Cancel changes nothing. After confirming the chip reads Paused and the row shows "last known status".
- The scan does not unpause it, and the Dashboard no longer counts it.
- Resume brings it back. The Activity Log has an entry for each pause and resume.

#### TC-DI-14 – Invalid pause and resume

**Requirement:** REQ-DI-12 · **Technique:** DT · **Priority:** M · **Result:** PASS

**Steps**

1. Open a Retired or Merged device's drawer and look for **Pause monitoring**.
2. On an already paused device look for **Pause monitoring**.
3. On a device that is not paused look for **Resume monitoring**.

**Expected result**

- Pause is not offered for Retired or Merged devices or for one already paused, and Resume is not offered for one that is not paused.
- If you send the request through the API instead, each returns 400 and nothing changes.

#### TC-DI-15 – Out-of-config devices show "last known status"

**Requirement:** REQ-DI-13 · **Technique:** EG · **Priority:** M · **Result:** PASS

**Steps**

1. Pause one device.
2. Open **Device Inventory** and read the default view, then change the Monitoring filter to **Paused**.
3. Read the summary above the table.

**Expected result**

- The page opens on **Monitored**, so the paused device is hidden until the filter changes.
- With the filter on **Paused** the row shows "last known status" under its chip.
- The summary counts monitored hosts only.

**9c. Device identity review and merging**

#### TC-DI-16 – Needs Review section

**Requirement:** REQ-DI-14 · **Technique:** DT · **Priority:** M · **Result:** PASS

**Steps**

1. As a user with `system.discover`, open **Device Inventory** when no identity issue is pending, then when some are.
2. Type a name in **Search hostname**.

**Expected result**

- The **Device identity reviews** section shows in both cases. When empty it reads "No device identity issues need review."
- Searching the host table does not change the review list.

#### TC-DI-17 – The review drawer writes nothing

**Requirement:** REQ-DI-14 · **Technique:** EP · **Priority:** M · **Result:** PASS

**Steps**

1. Press **Review** on an issue. The drawer **Review device identity** opens.
2. Read the two records side by side. Press **Load address history** once.
3. Close the drawer with **Close** or the Escape key.

**Expected result**

- Each record shows its stable device ID, Nagios host name, current IP, monitoring state, and identity confidence.
- Address history loads only after you press the button.
- Closing writes nothing and the issue stays unresolved.

#### TC-DI-18 – Merging needs edit permission and two distinct records

**Requirement:** REQ-DI-14 · **Technique:** DT · **Priority:** H · **Result:** PASS

**Steps**

1. As a user with `system.discover` and `system.hosts` but not `system.hosts.edit`, open a review drawer.
2. As Super Admin open the same drawer and look at **Device record to keep** and **Duplicate record to merge**.
3. Choose the same record in both.

**Expected result**

- Without `system.hosts.edit`, merging is not available.
- With it, neither list has a record chosen in advance.
- Choosing the same record twice is not allowed ("Choose two distinct records.").

#### TC-DI-19 – Merge confirmation

**Requirement:** REQ-DI-14 · **Technique:** ST · **Priority:** H · **Result:** PASS

**Steps**

1. Choose one record to keep and one to merge. Press **Review merge**.
2. Read the confirmation **Confirm device merge**.
3. Double-click **Merge duplicate**.

**Expected result**

- The confirmation lists both IDs, names, and IPs and says the source becomes Merged and leaves monitoring, the target's settings win in a conflict, and no undo is provided.
- A second click while saving is ignored.
- After success the review list and inventory refresh without a page reload.

### Module 10 – Topology (`/topology`)

**Summary of cases**

| TC | Case | Req | Tech | Pri | Result |
| --- | --- | --- | --- | --- | --- |
| TC-TOP-01 | Topology shows every device | TOP-01 | EP | H | PASS |
| TC-TOP-02 | Select a device; positions are fixed | TOP-01 | EP | M | PASS |
| TC-TOP-03 | Parent editor refuses bad parents | TOP-02 | DT | H | PASS |
| TC-TOP-04 | Save and clear parents | TOP-02 | EP | M | PASS |
| TC-TOP-05 | Only `system.hosts.edit` may change parents | TOP-03 | DT | H | PASS |
| TC-TOP-06 | Paused parent warning | TOP-02 | EG | L | PASS |

#### TC-TOP-01 – Topology shows every device

**Requirement:** REQ-TOP-01 · **Technique:** EP · **Priority:** H · **Result:** PASS

**Steps**

1. Open **Topology** ("Network Topology") on a lab with parents set, a paused device, and an unchecked device.

**Expected result**

- Every discovered device shows, including paused and unchecked ones and roots.
- A device with two parents appears under both.

#### TC-TOP-02 – Select a device; positions are fixed

**Requirement:** REQ-TOP-01 · **Technique:** EP · **Priority:** M · **Result:** PASS

**Steps**

1. Click a device. Read the panel **Device Information** and **Parent Relationship**.
2. Click **View child and parents** and then a relationship.
3. Try to drag a node.

**Expected result**

- The panel shows the device ID, host name, IP address, status, last check, and monitoring state.
- The relationship view shows the link.
- Nodes cannot be moved.

#### TC-TOP-03 – Parent editor refuses bad parents

**Requirement:** REQ-TOP-02 · **Technique:** DT · **Priority:** H · **Result:** PASS

**Steps**

1. In the device's **Parent devices** section tick the device itself (if offered), then a parent that would make a cycle, then a retired or merged device (if shown).
2. Press **Save parents** each time.

**Expected result**

- Each is refused with the server's message and your choices stay on screen. Nothing is saved.

#### TC-TOP-04 – Save and clear parents

**Requirement:** REQ-TOP-02 · **Technique:** EP · **Priority:** M · **Result:** PASS

**Steps**

1. Search a parent in **Search parent devices**, tick two, and press **Save parents**.
2. Press **Clear all** and **Save parents**.

**Expected result**

- "Parent devices saved." shows and both parents appear on the topology.
- After **Clear all** and save, the device has no parents ("No parent devices configured.").

#### TC-TOP-05 – Only `system.hosts.edit` may change parents

**Requirement:** REQ-TOP-03 · **Technique:** DT · **Priority:** H · **Result:** PASS

**Steps**

1. Sign in as a user with `system.network_health` and `system.hosts` but not `system.hosts.edit`. Open a device in **Topology**.
2. Open a Retired or Merged device as Super Admin.

**Expected result**

- The parents are visible and the note "Parent relationships are read-only." shows.
- Retired and merged devices are read-only for everyone.

#### TC-TOP-06 – Paused parent warning

**Requirement:** REQ-TOP-02 · **Technique:** EG · **Priority:** L · **Result:** PASS

**Steps**

1. Tick a paused device as a parent.

**Expected result**

- A warning says Nagios leaves a paused or address-unknown parent out.

## Test cases: operations modules

### Module 11 – Plugins (`/plugins`)

**Summary of cases**

| TC | Case | Req | Tech | Pri | Result |
| --- | --- | --- | --- | --- | --- |
| TC-PLG-01 | Category tabs | PLG-01 | EP | M | PASS |
| TC-PLG-02 | Banner when no plugin is enabled | PLG-02 | EG | M | PASS |
| TC-PLG-03 | Enable a plugin | PLG-03 | ST | H | PASS |
| TC-PLG-04 | Stop and resume one service | PLG-04 | ST | H | PASS |
| TC-PLG-05 | Custom checks need permission and support | PLG-05 | DT | M | PASS |
| TC-PLG-06 | Custom check password is masked | PLG-05 | EP | H | PASS |
| TC-PLG-07 | Plugins need permission | PLG-06 | DT | H | PASS |

The inventory has the tabs **All**, **Network Services**, **Device Availability**, **Network Protocols**, **Servers**, **Application**, and **Other**. Pressing a plugin opens its drawer with **Enable** or **Disable**, **Services**, and more.

#### TC-PLG-01 – Category tabs

**Requirement:** REQ-PLG-01 · **Technique:** EP · **Priority:** M · **Result:** PASS

**Steps**

1. Open **Plugins**.
2. Click each tab in turn and read the plugin list.
3. Go to page 2 of a tab, then switch tabs and come back.

**Expected result**

- Each tab lists only plugins of its category, and paging works within the tab.
- There is no "Currently Running" tab.

#### TC-PLG-02 – Banner when no plugin is enabled

**Requirement:** REQ-PLG-02 · **Technique:** EG · **Priority:** M · **Result:** PASS

**Before you start:** a fresh install where no plugin is enabled.

**Steps**

1. Open **Plugins**.
2. Read the banner and the **Monitoring** column.

**Expected result**

- A banner says no plugin is enabled, and no plugin is shown as monitoring.

#### TC-PLG-03 – Enable a plugin

**Requirement:** REQ-PLG-03 · **Technique:** ST · **Priority:** H · **Result:** PASS

**Steps**

1. Press a disabled plugin (for example `check_http`) to open its drawer.
2. Press **Enable** and read the preview of what will be monitored.
3. Press **Cancel**. Press **Enable** again and then **Confirm enable**.
4. Look at the **Services** section of the drawer.

**Expected result**

- The preview lists what will be monitored.
- Cancel changes nothing. After **Confirm enable** the plugin is Enabled and its services appear (or the drawer says they attach as devices are found).

#### TC-PLG-04 – Stop and resume one service

**Requirement:** REQ-PLG-04 · **Technique:** ST · **Priority:** H · **Result:** PASS

**Steps**

1. In an enabled plugin's drawer find **Monitored services** and type a device name in **Search monitored services**.
2. Press **Stop monitoring** on one device's service.
3. Look at **System Status**.
4. Return and press **Resume monitoring**.

**Expected result**

- The search narrows the list.
- After stopping, that device's service shows as Stopped and leaves **System Status**.
- After resuming it is monitored again.

#### TC-PLG-05 – Custom checks need permission and support

**Requirement:** REQ-PLG-05 · **Technique:** DT · **Priority:** M · **Result:** PASS

**Steps**

1. As Super Admin open a plugin that supports custom checks and read its drawer.
2. Open a plugin that does not support them.
3. Sign in as a user with `plugin.view` but not `plugin.custom_check` and open the first plugin again.

**Expected result**

- The custom checks section shows only for a plugin that supports them and only with `plugin.custom_check`.
- The other plugin says "Not service-driven."

#### TC-PLG-06 – Custom check password is masked

**Requirement:** REQ-PLG-05 · **Technique:** EP · **Priority:** H · **Result:** PASS

**Steps**

1. In a supporting plugin press **Add check**. Choose a device in **Device** (search by name or IP), type a **Name**, and type a password.
2. Save, then open the check again.

**Expected result**

- The password field is masked while you type.
- When reopened it is never shown. It says "Stored. Leave blank to keep it."

#### TC-PLG-07 – Plugins need permission

**Requirement:** REQ-PLG-06 · **Technique:** DT · **Priority:** H · **Result:** PASS

**Steps**

1. Sign in as the Staff user.
2. Type `/plugins` in the address bar. Open `/api/plugin/summary`.

**Expected result**

- **Plugins** is not in the sidebar, the address redirects away, and the API returns 403.

### Module 12 – NCPA Deployment (`/ncpa-deployment`)

**Summary of cases**

| TC | Case | Req | Tech | Pri | Result |
| --- | --- | --- | --- | --- | --- |
| TC-NCPA-01 | Warning when `check_ncpa` is off | NCPA-01 | EG | M | PASS |
| TC-NCPA-02 | Deploy wizard order | NCPA-02 | ST | H | PASS |
| TC-NCPA-03 | Wrong and right SSH password | NCPA-02 | EP | H | PASS |
| TC-NCPA-04 | Run progress and history | NCPA-03 | ST | H | PASS |
| TC-NCPA-05 | Who can use Clean up | NCPA-04 | DT | M | PASS |
| TC-NCPA-06 | Clean up | NCPA-04 | EP | H | PASS |
| TC-NCPA-07 | No credentials shown anywhere | NCPA-05 | EG | H | PASS |
| TC-NCPA-08 | NCPA Deployment needs permission | NCPA-06 | DT | H | PASS |
| TC-NCPA-09 | Remote restart settings (issue #182) | NCPA-07 | EP | M | PASS |
| TC-NCPA-10 | Remote restart is blocked during a deployment | NCPA-07 | EG | M | PASS |
| TC-NCPA-11 | Clean up warns that remote restarts stop | NCPA-08 | EG | M | PASS |

The page has the **Devices** tab (a table with **Select**, **Device**, **IP Address**, **Agent**, **Host Key**, **Last Result**, **Actions**) and a **Deployment History** tab. Buttons: **Deploy selected**, **Verify**, **Clean up**, **Remote restart**.

#### TC-NCPA-01 – Warning when check\_ncpa is off

**Requirement:** REQ-NCPA-01 · **Technique:** EG · **Priority:** M · **Result:** PASS

**Steps**

1. In **Plugins** make sure `check_ncpa` is disabled.
2. Open **NCPA Deployment**.
3. Enable `check_ncpa` and reopen the page.

**Expected result**

- A warning says the agent's checks are monitored only while `check_ncpa` is enabled.
- The warning is gone once it is enabled.

#### TC-NCPA-02 – Deploy wizard order

**Requirement:** REQ-NCPA-02 · **Technique:** ST · **Priority:** H · **Result:** PASS

**Before you start:** a Linux VM with SSH, found by a scan, and `check_ncpa` enabled.

**Steps**

1. In the **Devices** table press **Verify** on the VM and compare the fingerprint, then press **Trust**.
2. Tick the VM and press **Deploy selected**. The wizard "Deploy NCPA" opens.
3. Go through **Verify host keys**, **Check logins**, and then deploy.
4. Try to go forward from **Check logins** before the host key is trusted (use a second VM that is not trusted).

**Expected result**

- Each step must pass before the next one is available.
- An untrusted host key stops the run ("Its host key is not trusted yet.") and a changed key says to remove it and verify again.

#### TC-NCPA-03 – Wrong and right SSH password

**Requirement:** REQ-NCPA-02 · **Technique:** EP · **Priority:** H · **Result:** PASS

**Steps**

1. In the wizard, at **Credentials**, type the correct username and a wrong **Password**. Press **Check logins**.
2. Type the correct password and press **Check logins** again.
3. On a VM whose account cannot use sudo, check logins once.

**Expected result**

- Wrong password: "Rejected this username or password." and nothing starts.
- Correct password: "Login and sudo verified." and the deploy step is available.
- No sudo: "Logged in, but this account cannot use sudo."

#### TC-NCPA-04 – Run progress and history

**Requirement:** REQ-NCPA-03 · **Technique:** ST · **Priority:** H · **Result:** PASS

**Steps**

1. Start the deployment and stay on the page.
2. Watch the run banner until it finishes.
3. Open the **Deployment History** tab and press the new run.

**Expected result**

- A live banner shows progress until the run ends with Success.
- History lists the run with its outcome. The run drawer shows each step, who started it, and when.
- Starting a second deployment while one is running is refused ("A deployment is already running.").

#### TC-NCPA-05 – Who can use Clean up

**Requirement:** REQ-NCPA-04 · **Technique:** DT · **Priority:** M · **Result:** PASS

**Steps**

1. Look at the **Actions** column of the **Devices** table for: a trusted device whose deployment failed, a successfully deployed device, and a device never deployed.

**Expected result**

- **Clean up** is shown for the trusted failed device and for the deployed device (since issue #182).
- It is not shown for a device that was never deployed.

#### TC-NCPA-06 – Clean up

**Requirement:** REQ-NCPA-04 · **Technique:** EP · **Priority:** H · **Result:** PASS

**Steps**

1. Press **Clean up** on a trusted failed device.
2. Type **SSH username** and **SSH password**. Tick "Also remove the Pinpoint deployment account" only for one run.
3. Press **Run cleanup**. Read each step result.
4. Close the dialog and reopen it.

**Expected result**

- Each cleanup step shows its result, and the end message reads "Cleanup completed. Device is ready to deploy again." or "Cleanup incomplete; review the steps and retry."
- After the dialog is reopened the username and password fields are empty.

#### TC-NCPA-07 – No credentials shown anywhere

**Requirement:** REQ-NCPA-05 · **Technique:** EG · **Priority:** H · **Result:** PASS

**Steps**

1. After a deployment read the run drawer in **Deployment History**.
2. Open `/api/system/deployment/ncpa/runs` in the address bar (or the history route shown in the browser's network tab).

**Expected result**

- No password, private key, or token appears in the drawer or in the API text.

#### TC-NCPA-08 – NCPA Deployment needs permission

**Requirement:** REQ-NCPA-06 · **Technique:** DT · **Priority:** H · **Result:** PASS

**Steps**

1. Sign in as the Staff user.
2. Type `/ncpa-deployment` in the address bar.

**Expected result**

- The page is not in the sidebar and the address redirects to Settings.

#### TC-NCPA-09 – Remote restart settings (issue #182)

**Requirement:** REQ-NCPA-07 · **Technique:** EP · **Priority:** M · **Result:** PASS

**Before you start:** a trusted device (host key verified).

**Steps**

1. On the device's row press **Remote restart**. The dialog shows "Loading restart settings…" and then its fields.
2. Under **Services allowed to restart** type one service name per line (for example `apache2`). Leave **Allow remote service restart** off. Press **Save settings**.
3. Reopen the dialog.
4. Type 21 service names and save.
5. Try to switch **Allow remote service restart** on for a device that is not trusted.

**Expected result**

- The list saves with the switch off, and the same list shows when reopened.
- At most 20 service names are accepted (the 21st is refused with a message).
- The switch cannot be turned on without a confirmed host key and an installed deployment key. An empty list says "No services are allowed until you add them."

#### TC-NCPA-10 – Remote restart is blocked during a deployment

**Requirement:** REQ-NCPA-07 · **Technique:** EG · **Priority:** M · **Result:** PASS

**Steps**

1. Start a deployment on one device.
2. While it runs, press **Remote restart** on any device.
3. Press **Retry** if a load error shows.

**Expected result**

- Settings cannot be opened while a deployment is running.
- Loading and save errors show a message with **Retry**.

#### TC-NCPA-11 – Clean up warns that remote restarts stop

**Requirement:** REQ-NCPA-08 · **Technique:** EG · **Priority:** M · **Result:** PASS

**Steps**

1. Press **Clean up** on a deployed device that has remote restart enabled.
2. Read the text in the dialog.
3. Run cleanup, then look at that device's **Remote restart** dialog.

**Expected result**

- The dialog warns that remote restarts stop until the device is deployed again.
- Credentials are cleared after the request. The saved service list in Pinpoint remains.

### Module 13 – Maintenance (`/maintenance`)

**Summary of cases**

| TC | Case | Req | Tech | Pri | Result |
| --- | --- | --- | --- | --- | --- |
| TC-MNT-01 | Empty state | MNT-01 | EG | L | PASS |
| TC-MNT-02 | Create a window | MNT-02 | EP | H | PASS |
| TC-MNT-03 | The 30-day limit | MNT-02 | BVA | H | PASS |
| TC-MNT-04 | Invalid time ranges | MNT-02 | BVA | M | PASS |
| TC-MNT-05 | Repeat end limit | MNT-02 | BVA | M | PASS |
| TC-MNT-06 | Reason length | MNT-02 | BVA | M | PASS |
| TC-MNT-07 | Cancel a window | MNT-03 | ST | H | PASS |
| TC-MNT-08 | Cancel while Nagios cannot be told | MNT-04 | EG | M | PASS |
| TC-MNT-09 | Device choices and permission | MNT-05 | DT | H | PASS |
| TC-MNT-10 | An active window silences alerts | MNT-06 | ST | H | PASS |

The page lists **Windows** with the columns **Devices**, **Next occurrence**, **Repeats**, **Status**, **Reason**, and **Actions**. **New window** opens a form with **Devices**, **Repeats**, **Starts**, **Ends**, **Stop repeating after (optional)**, and **Reason**.

#### TC-MNT-01 – Empty state

**Requirement:** REQ-MNT-01 · **Technique:** EG · **Priority:** L · **Result:** PASS

**Steps**

1. Open **Maintenance** when no window exists.

**Expected result**

- The page says "No maintenance windows yet. Create one before planned work to stop alerts for it."

#### TC-MNT-02 – Create a window

**Requirement:** REQ-MNT-02 · **Technique:** EP · **Priority:** H · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-18-module-13-maintenance/REPORT.md)

**Steps**

1. Press **New window**.
2. In **Devices** choose one monitored device. Set **Repeats** to **Does not repeat**.
3. Set **Starts** to one hour from now and **Ends** to two hours from now. Type a **Reason** such as `kernel updates`.
4. Press **Create window**.
5. Open **System Logs**, tab **Activity Log**.

**Expected result**

- "Maintenance window created." shows and the window is listed as **Scheduled** with its next occurrence.
- The Activity Log records it.

#### TC-MNT-03 – The 30-day limit

**Requirement:** REQ-MNT-02 · **Technique:** BVA · **Priority:** H · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-18-module-13-maintenance/REPORT.md)

**Steps**

1. Press **New window** and set **Repeats** to **Does not repeat**.
2. Set **Starts** to tomorrow 09:00 and **Ends** exactly 30 days later at 09:00. Press **Create window**.
3. Change **Ends** to 30 days and 1 minute after **Starts** and try again.

**Expected result**

- 30 days is accepted.
- 30 days and 1 minute is refused by the form before anything is sent.

#### TC-MNT-04 – Invalid time ranges

**Requirement:** REQ-MNT-02 · **Technique:** BVA · **Priority:** M · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-18-module-13-maintenance/REPORT.md)

**Steps**

1. Try to create a window where **Ends** is before **Starts**.
2. Try one whose end is already in the past.
3. Set **Repeats** to **Every day** with a window of 25 hours.
4. Set **Repeats** to **Every week** with a window of 8 days.

**Expected result**

- Each is refused with a message, and the form stays open with your entries.
- A daily window may last up to 1 day and a weekly window up to 7 days.

#### TC-MNT-05 – Repeat end limit

**Requirement:** REQ-MNT-02 · **Technique:** BVA · **Priority:** M · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-18-module-13-maintenance/REPORT.md)

**Steps**

1. Set **Repeats** to **Every day** and a valid short window.
2. Set **Stop repeating after (optional)** to 366 days after **Starts** and press **Create window**.
3. Edit it and set 367 days.

**Expected result**

- 366 days is accepted and 367 days is refused.

#### TC-MNT-06 – Reason length

**Requirement:** REQ-MNT-02 · **Technique:** BVA · **Priority:** M · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-18-module-13-maintenance/REPORT.md)

**Steps**

1. Create a window with an empty **Reason**.
2. Create one with a 1-character reason.
3. Create one with a 200-character reason.
4. Create one with a 201-character reason.

**Expected result**

- 0 and 201 characters are refused. 1 and 200 are accepted.

#### TC-MNT-07 – Cancel a window

**Requirement:** REQ-MNT-03 · **Technique:** ST · **Priority:** H · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-18-module-13-maintenance/REPORT.md)

**Steps**

1. In the **Actions** column of a Scheduled window press **Cancel**. Read "Cancel this window?".
2. Press **Keep it**.
3. Press **Cancel** again and press **Yes, cancel it**.

**Expected result**

- **Keep it** changes nothing.
- **Yes, cancel it** sets the status to **Cancelled** and shows "Maintenance window cancelled." Pending and running downtime for the devices ends.

#### TC-MNT-08 – Cancel while Nagios cannot be told

**Requirement:** REQ-MNT-04 · **Technique:** EG · **Priority:** M · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-18-module-13-maintenance/REPORT.md)

**Steps**

1. Stop Nagios on the appliance (`systemctl stop nagios`).
2. Cancel a window as in TC-MNT-07.
3. Start Nagios again.

**Expected result**

- The window is still cancelled, and a notice says Nagios was not updated.

#### TC-MNT-09 – Device choices and permission

**Requirement:** REQ-MNT-05 · **Technique:** DT · **Priority:** H · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-18-module-13-maintenance/REPORT.md)

**Steps**

1. Have one paused, one retired, and one missing device on the lab. Open **New window** and open **Devices**.
2. Sign in as the Staff user and type `/maintenance` in the address bar.

**Expected result**

- Paused, retired, and missing devices cannot be chosen. **All monitored devices** is offered.
- The Staff user is redirected to Settings and **Maintenance** is not in the sidebar.

#### TC-MNT-10 – An active window silences alerts

**Requirement:** REQ-MNT-06 · **Technique:** ST · **Priority:** H · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-18-module-13-maintenance/REPORT.md)

**Before you start:** the email settings work (TC-SET-07).

**Steps**

1. Create a window for the web VM that starts in 15 minutes and ends in 1 hour.
2. Wait until it is active. Stop the web server on the VM.
3. Wait for the check and retry time. Open **Overview** and the mailbox.

**Expected result**

- The host or service shows the scheduled downtime indicator.
- The service shows Critical, but no notification email is sent for it.

### Module 14 – Remediation (`/remediation`)

**Summary of cases**

| TC | Case | Req | Tech | Pri | Result |
| --- | --- | --- | --- | --- | --- |
| TC-REM-01 | Read-only view | REM-01 | DT | H | PASS |
| TC-REM-02 | Add and edit an action | REM-02 | EP | H | PASS |
| TC-REM-03 | Enable, disable, and delete | REM-03 | ST | M | PASS |
| TC-REM-04 | Changes need `remediation.manage` | REM-04 | DT | H | PARTIALLY PASS |
| TC-REM-05 | Conflict and Nagios errors | REM-05 | EG | M | PASS |
| TC-REM-06 | Run log | REM-06 | EP | M | PASS |
| TC-REM-07 | The kill switch (issue #155) | REM-07 | ST | H | PASS |
| TC-REM-08 | Health panel and stalled warning (issue #155) | REM-08 | EG | M | PASS |
| TC-REM-09 | Acknowledged problems and "Run when acknowledged" (issue #155) | REM-09 | DT | M | PASS |
| TC-REM-10 | Action parameters per type (issue #182) | REM-10 | EP | M | PASS |

Above the tabs a status panel shows **Automatic recovery** (the kill switch) and its health. The tabs are **Actions** (banner "Actions run automatically when a service reaches a hard failure.") and **Run log**.

#### TC-REM-01 – Read-only view

**Requirement:** REQ-REM-01 · **Technique:** DT · **Priority:** H · **Result:** PASS

**Before you start:** a user whose role has `remediation.view` but not `remediation.manage`.

**Steps**

1. Sign in as that user and open **Remediation**.
2. Look for **Add action**, the enable switches, edit and delete, and the **Automatic recovery** switch.

**Expected result**

- The actions are listed, but nothing can be added, edited, enabled, or deleted.
- The kill switch is disabled and says "You need the remediation manage permission to change this."

#### TC-REM-02 – Add and edit an action

**Requirement:** REQ-REM-02 · **Technique:** EP · **Priority:** H · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-19-module-14-remediation/REPORT.md)

**Steps**

1. As a user with `remediation.manage` press **Add action**.
2. Type a **Name**, choose **Action type** "Record only", set **Scope** to a service, choose a service or type a **Service pattern**, and keep **Cooldown (seconds)** and **Max runs per hour** at their defaults. Press **Save action**.
3. Press **Add action** again and enter a **Cooldown (seconds)** below 60 (for example 10).
4. Edit the first action and change its name.

**Expected result**

- The valid action is saved and listed.
- The invalid value is refused with a message beside that field (cooldown 60 seconds to 24 hours, runs per hour 1 to 60).
- The edit is saved.

#### TC-REM-03 – Enable, disable, and delete

**Requirement:** REQ-REM-03 · **Technique:** ST · **Priority:** M · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-19-module-14-remediation/REPORT.md)

**Steps**

1. Switch an action's enable switch off and on.
2. Press delete on an action, cancel, then delete again and confirm.

**Expected result**

- The switch changes the action's state and the list shows it.
- Cancel keeps the action. Confirming removes it. Its past runs stay in the **Run log** (with the action link cleared).

#### TC-REM-04 – Changes need `remediation.manage`

**Requirement:** REQ-REM-04 · **Technique:** DT · **Priority:** H · **Result:** PARTIALLY PASS -

**Before you start:** the same user as TC-REM-01.

**Steps**

1. Open **Remediation** as that user.
2. Try each control: **Add action**, an enable switch, an action's edit and delete, the **Automatic recovery** switch.
3. If you have a tool such as curl and the session cookie, send a `PUT` to `/api/system/remediation/settings`.

**Expected result**

- Every control is disabled or missing, and any change request returns 403.
- (The previous result note is empty. Write down which control was still usable.)

#### TC-REM-05 – Conflict and Nagios errors

**Requirement:** REQ-REM-05 · **Technique:** EG · **Priority:** M · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-19-module-14-remediation/REPORT.md)

**Steps**

1. Open the same action in two browsers. Change and save it in the first.
2. In the second change it and save.
3. Save an action that Nagios rejects (for example by breaking the Nagios config in the lab first).

**Expected result**

- The second save is refused with a conflict (409) and offers **Reload**.
- A Nagios rejection (422) shows the Nagios message and nothing is kept.

#### TC-REM-06 – Run log

**Requirement:** REQ-REM-06 · **Technique:** EP · **Priority:** M · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-19-module-14-remediation/REPORT.md)

**Steps**

1. Open the **Run log** tab. Read **Time**, **Action**, **Host**, **Service**, **State**, **Outcome**, and **Reason**.
2. Filter by **All actions**, **All outcomes**, **Host**, **From**, and a date range.
3. Press **Details** on a run.

**Expected result**

- Each filter narrows the list, and paging works.
- A skipped run shows its reason.
- The detail drawer shows the outcome without any secret in the output.

#### TC-REM-07 – The kill switch (issue #155)

**Requirement:** REQ-REM-07 · **Technique:** ST · **Priority:** H · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-19-module-14-remediation/REPORT.md)

**Before you start:** one enabled action covering a service you can break, and a user with `remediation.manage`.

**Steps**

1. In the status panel switch **Automatic recovery** off. Read the confirmation, cancel, then switch it off again and confirm.
2. Reload the page.
3. Break the covered service so it reaches a hard failure. Open the **Run log**.
4. Switch **Automatic recovery** on again and confirm ("Resume automatic recovery? Enabled actions will run again on the next hard failure.").

**Expected result**

- Cancel changes nothing. After confirming the panel says "Stopped. No action runs; each covered failure is logged as skipped." and it stays stopped after a reload.
- The covered failure is logged as skipped by the kill switch, and no action ran. The **Actions** tab notes "Paused by the kill switch".
- After switching on, the panel says "On. Enabled actions run when a covered failure becomes a hard failure."

#### TC-REM-08 – Health panel and stalled warning (issue #155)

**Requirement:** REQ-REM-08 · **Technique:** EG · **Priority:** M · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-19-module-14-remediation/REPORT.md)

**Steps**

1. Read the status panel: last check-in, events waiting, runs (24 h), limits hit (24 h), skipped (24 h), and events dropped.
2. Wait 30 seconds and read it again (it refreshes every 15 seconds).
3. On the appliance stop the Pinpoint service for more than 45 seconds and open the page on another device, or read it right after a restart.

**Expected result**

- The numbers show and refresh.
- When the consumer has not checked in for about 45 seconds, a red banner says "Automatic recovery has stopped checking in."

#### TC-REM-09 – Acknowledged problems and "Run when acknowledged" (issue #155)

**Requirement:** REQ-REM-09 · **Technique:** DT · **Priority:** M · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-19-module-14-remediation/REPORT.md)

**Steps**

1. Create action A without **Run when acknowledged** and action B with it ticked. Both cover the same service and use "Record only".
2. Break the service, acknowledge the alert before the hard failure, and wait for the hard failure.
3. Open the **Run log**.

**Expected result**

- Action A is logged as skipped because the problem was acknowledged.
- Action B runs (a record is written).

#### TC-REM-10 – Action parameters per type (issue #182)

**Requirement:** REQ-REM-10 · **Technique:** EP · **Priority:** M · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-19-module-14-remediation/REPORT.md)

**Steps**

1. Press **Add action**. Choose **Action type** "Restart a PinPoint host service" and look at the unit field.
2. Switch **Action type** to "Restart a service on the monitored device" and look at the field.
3. Type `my service!` and save, then `apache2` and save.
4. Switch the type back and forth once more.

**Expected result**

- The local type offers a fixed list (only `nagios` today). The remote type offers a text box for **Service to restart**.
- A name with a space or `!` is refused beside the field. A plain name is accepted (letters, digits, dots, underscores, @, and dashes, starting with a letter or digit, up to 63 characters).
- Switching the type clears the old type's parameters.

## Test cases: reports, logs, and settings

### Module 15 – Reports (sidebar: Report, `/reports`)

**Summary of cases**

| TC | Case | Req | Tech | Pri | Result |
| --- | --- | --- | --- | --- | --- |
| TC-RPT-01 | Host Availability report | RPT-01 | EP | H | FAIL (initial main-lab run; temporary scratch retest PASS; post-merge confirmation not recorded) |
| TC-RPT-02 | Network Services report | RPT-02 | EP | H | PASS |
| TC-RPT-03 | CSV and Excel export | RPT-03 | EP | M | PASS |
| TC-RPT-04 | PDF print view | RPT-03 | EP | L | PASS |
| TC-RPT-05 | Exports are logged | RPT-04 | DT | M | PASS |
| TC-RPT-06 | A period with no data | RPT-05 | EG | M | PARTIALLY PASS (initial main-lab run; temporary scratch retest PASS; post-merge confirmation not recorded) |
| TC-RPT-07 | Reports need permission | RPT-06 | DT | H | PASS |

The tabs are **Host Availability**, **Network Services**, **Hosts by OS**, **Device Services**, **Alerts**, and **Notifications**. Choose a period (**Last 24 hours**, **Today**, **Last 7 days**, **Last 30 days**, **Last 90 days**, or **Custom range**) and press **Run Report**. The **Export** menu offers CSV, Excel, and PDF.

#### TC-RPT-01 – Host Availability report

**Requirement:** REQ-RPT-01 · **Technique:** EP · **Priority:** H · **Result:** FAIL (initial main-lab run; temporary scratch retest PASS; post-merge confirmation not recorded)

**Recorded run:** [report](../test-runs/2026-10-19-module-15-reports/REPORT.md) · **Retest:** [temporary scratch build report](../test-runs/2026-10-19-module-15-reports-retest/REPORT.md)

**Steps**

1. Open **Report** and choose the **Host Availability** tab.
2. Set the period to **Last 24 hours** and press **Run Report**.
3. Open **Device Inventory** (Monitored filter) and count the hosts.

**Expected result**

- One row per monitored host with its state, **Uptime %**, and last check.
- Every uptime value is between 0 and 100.
- The number of rows equals the monitored hosts in Device Inventory.

#### TC-RPT-02 – Network Services report

**Requirement:** REQ-RPT-02 · **Technique:** EP · **Priority:** H · **Result:** PASS

**Steps**

1. Choose the **Network Services** tab, **Last 24 hours**, and press **Run Report**.
2. Compare one service's counts with **System Status**.

**Expected result**

- One row per service name with OK, Warning, and Critical totals across hosts.
- The totals match **System Status** for the current state.

#### TC-RPT-03 – CSV and Excel export

**Requirement:** REQ-RPT-03 · **Technique:** EP · **Priority:** M · **Result:** PASS

**Steps**

1. After running the Host Availability report press **Export** and choose CSV.
2. Press **Export** again and choose Excel.
3. Open both downloads.

**Expected result**

- A `.csv` file with a header row and as many data rows as the table.
- A `.xls` file (an HTML table that Excel opens) with the same rows.

#### TC-RPT-04 – PDF print view

**Requirement:** REQ-RPT-03 · **Technique:** EP · **Priority:** L · **Result:** PASS

**Steps**

1. Press **Export** and choose PDF.
2. In the print window choose **Save as PDF** and save it.

**Expected result**

- A print-formatted view opens with the same rows, and the saved PDF is readable. (There is no PDF library, so the browser's print dialog does the saving.)

#### TC-RPT-05 – Exports are logged

**Requirement:** REQ-RPT-04 · **Technique:** DT · **Priority:** M · **Result:** PASS

**Steps**

1. After the three exports open **System Logs** and the **Export Log** tab.

**Expected result**

- One entry per export with who exported, the report type, the format, the period, and the time.

#### TC-RPT-06 – A period with no data

**Requirement:** REQ-RPT-05 · **Technique:** EG · **Priority:** M · **Result:** PARTIALLY PASS (initial main-lab run; temporary scratch retest PASS; post-merge confirmation not recorded)

**Recorded run:** [report](../test-runs/2026-10-19-module-15-reports/REPORT.md) · **Retest:** [temporary scratch build report](../test-runs/2026-10-19-module-15-reports-retest/REPORT.md)

**Steps**

1. Choose **Custom range**, pick a start and end date from before the install, and press **Run Report**.

**Expected result**

- A message such as "No data in this period" shows, not an error or a blank page.

#### TC-RPT-07 – Reports need permission

**Requirement:** REQ-RPT-06 · **Technique:** DT · **Priority:** H · **Result:** PASS

**Steps**

1. Sign in as the Staff user.
2. Type `/reports` in the address bar. Open `/api/system/report/availability`.

**Expected result**

- **Report** is not in the sidebar, the address redirects away, and the API returns 403.

### Module 16 – System Logs (`/system-logs`)

**Summary of cases**

| TC | Case | Req | Tech | Pri | Result |
| --- | --- | --- | --- | --- | --- |
| TC-LOG-01 | The five audit logs | LOG-01 | EP | M | PASS |
| TC-LOG-02 | An action is logged | LOG-01 | ST | H | PASS |
| TC-LOG-03 | Nagios log shows at most 200 lines | LOG-02 | BVA | M | PASS |
| TC-LOG-04 | Nagios log hides free text | LOG-03 | EG | H | PASS |
| TC-LOG-05 | System Logs need permission | LOG-04 | DT | H | PASS |

The tabs are **Activity Log**, **Configuration Change**, **Network Discovery**, **NCPA Deployment**, **Export Log**, and **Nagios log**. The first five are the audit logs.

#### TC-LOG-01 – The five audit logs

**Requirement:** REQ-LOG-01 · **Technique:** EP · **Priority:** M · **Result:** PASS

**Steps**

1. Open **System Logs**. Click each of the five audit tabs.
2. On one tab type text in **Search**, open the filter, and open the export menu.
3. Click a row to read its details.

**Expected result**

- Each tab lists its entries with a **Timestamp**.
- Search and the filter narrow the rows, the export menu downloads them, and a row opens its details.

#### TC-LOG-02 – An action is logged

**Requirement:** REQ-LOG-01 · **Technique:** ST · **Priority:** H · **Result:** PASS

**Steps**

1. Create a role in **Manage Roles**.
2. Open **System Logs**, **Activity Log**.
3. Change a setting in **Settings** and open **Configuration Change**.

**Expected result**

- The role creation is in the **Activity Log** with the user, the action, and the time.
- The setting change is in **Configuration Change**.

#### TC-LOG-03 – Nagios log shows at most 200 lines

**Requirement:** REQ-LOG-02 · **Technique:** BVA · **Priority:** M · **Result:** PASS

**Steps**

1. Open the **Nagios log** tab on a lab whose Nagios log has more than 200 lines.
2. Count the lines and read their order.
3. Cause a new Nagios event (restart a service), then press **Refresh Nagios log**.

**Expected result**

- At most 200 lines show (from the last 64 KiB), oldest at the top and newest at the bottom.
- **Refresh Nagios log** brings in the new entry.

#### TC-LOG-04 – Nagios log hides free text

**Requirement:** REQ-LOG-03 · **Technique:** EG · **Priority:** H · **Result:** PASS

**Result confirmation:** Manual PASS confirmed by the lab owner in this conversation on 2026-10-19; recorded here without a new execution.

**Steps**

1. With the configured Nagios log readable, compare an actual host or service state record on the appliance with the same record in **System Logs → Nagios log**. Use a record whose raw line includes plugin output. Confirm that the page retains its state fields while hiding the plugin output. Also check a command or other free-text message: its contents must be hidden.
2. In the disposable lab, record the configured log file's original owner and permissions, then temporarily make that file unreadable by the account running Pinpoint. Reopen the **Nagios log** tab or press **Refresh Nagios log** and check the unavailable message. This is a file-read failure check; Nagios itself does not need to be stopped.
3. Restore the original owner and permissions. Refresh the tab and confirm the log is readable again.

**Expected result**

- Host and service state fields stay readable; plugin output is replaced by `[output redacted]`. Commands and other free text are replaced by `[message redacted]`.
- When Pinpoint cannot read the configured file, the page shows "Nagios log is unavailable. The server could not read the configured log file."
- After access is restored, the log loads again.

#### TC-LOG-05 – System Logs need permission

**Requirement:** REQ-LOG-04 · **Technique:** DT · **Priority:** H · **Result:** PASS

**Steps**

1. Sign in as the Staff user.
2. Type `/system-logs` in the address bar. Open `/api/system/log`.

**Expected result**

- **System Logs** is not in the sidebar, the address redirects away, and the API returns 403.

### Module 17 – Settings (`/settings`)

**Summary of cases**

| TC | Case | Req | Tech | Pri | Result |
| --- | --- | --- | --- | --- | --- |
| TC-SET-01 | Dashboard Refresh Rate | SET-01 | EP | M | PASS |
| TC-SET-02 | Data polling interval | SET-02 | BVA | M | PASS |
| TC-SET-03 | Check interval and retry interval | SET-03 | BVA | H | PASS |
| TC-SET-04 | Maximum check attempts | SET-03 | BVA | M | PASS |
| TC-SET-05 | Flap thresholds | SET-04 | BVA | M | PASS |
| TC-SET-06 | Notification policy | SET-05 | EP | H | PASS |
| TC-SET-07 | Email (SMTP) settings | SET-06 | EP | H | PASS |
| TC-SET-08 | A failed save restores the old values | SET-07 | ST | H | PASS |
| TC-SET-09 | Maintenance Mode | SET-07 | EG | M | PASS |

Changes are saved with **Save Changes**. **Discard Changes** and **Reset to Defaults** are next to it.

#### TC-SET-01 – Dashboard Refresh Rate

**Requirement:** REQ-SET-01 · **Technique:** EP · **Priority:** M · **Result:** PASS

**Steps**

1. Open **Settings**, **General Settings**, and find **Dashboard Refresh Rate**.
2. Choose each option (**Auto Refresh - 1 minute**, **Auto Refresh - 5 minutes**, **Auto Refresh - 15 minutes**, **Manual**) and press **Save Changes** each time.
3. Open **Overview** and read the header line. Sign in as another user and read theirs.

**Expected result**

- The header reads "Auto-refreshing every N min" or "Auto-refresh: Manual" for the chosen option.
- The setting belongs to your account only.

#### TC-SET-02 – Data polling interval

**Requirement:** REQ-SET-02 · **Technique:** BVA · **Priority:** M · **Result:** PASS

**Steps**

1. Open **Settings**, **System**, and find **Data polling interval**.
2. Open the list and read the options. Pick one and press **Save Changes**.
3. Restart the Pinpoint service and read the value again.

**Expected result**

- Only 30, 60, 120, and 300 seconds are offered (default 60).
- The saved value takes effect without a restart and is still saved after a restart.

#### TC-SET-03 – Check interval and retry interval

**Requirement:** REQ-SET-03 · **Technique:** BVA · **Priority:** H · **Result:** PASS

**Steps**

1. In **Settings**, **System** open **Check interval** and read the options.
2. Set **Check interval** to 10 minutes and **Retry interval** to 5 minutes. Save.
3. Open **Retry interval** and read the options.
4. Lower **Check interval** to 2 minutes and read **Retry interval**.

**Expected result**

- **Check interval** offers 1, 2, 5, 10, and 15 minutes (default 5).
- **Retry interval** offers only values from 1 up to the **Check interval**, up to 10 minutes (default 1).
- Lowering the check interval lowers the retry interval with it.
- A save that Nagios cannot apply shows an error and restores the old values.

#### TC-SET-04 – Maximum check attempts

**Requirement:** REQ-SET-03 · **Technique:** BVA · **Priority:** M · **Result:** PASS

**Steps**

1. In **Settings**, **System** open **Maximum check attempts**.
2. Read the range of values and the help text.
3. Pick 1 and save, then pick 10 and save.

**Expected result**

- Values run from 1 to 10 (default 3). 0 and 11 cannot be chosen (if you send them through the API they are refused).
- The help text says more attempts means slower alerts and fewer false alarms.

#### TC-SET-05 – Flap thresholds

**Requirement:** REQ-SET-04 · **Technique:** BVA · **Priority:** M · **Result:** PASS

**Result confirmation:** Manual PASS confirmed by the lab owner in this conversation on 2026-10-19; recorded here without a new execution.

**Steps**

1. In **Settings**, **System** find **Flap detection**, **Low flap threshold**, and **High flap threshold**.
2. Enter -1 in the low box, then 0, then 100. Enter 101 in the high box.
3. Enter a low value of 30 and a high value of 20.
4. Clear both boxes and save.

**Expected result**

- 0 and 100 are accepted. -1 and 101 show "Flap thresholds must be a percentage from 0 to 100." and are not sent.
- A low value that is not below the high one shows "The low flap threshold must be lower than the high flap threshold."
- Empty boxes use Nagios's own values (shown as "Nagios default", 5 and 20 percent).

#### TC-SET-06 – Notification policy

**Requirement:** REQ-SET-05 · **Technique:** EP · **Priority:** H · **Result:** PASS

**Steps**

1. In **Settings**, **System** find the card **Notification policy**.
2. Press **Add quiet hours**, enter an end time before the start time, and save.
3. Add two quiet-hour periods on the same weekday that overlap, and save.
4. Untick every notification option for hosts and services and save.
5. Type 1441 in **Renotify interval (minutes)** and save.
6. Enter a valid policy and save.

**Expected result**

- Each bad entry is refused with a message before saving (for example "Quiet hours on the same weekday must not overlap.", "Select at least one host and service notification option.", "Renotify interval must be from 0 to 1440 minutes.").
- A valid policy saves ("Policy saved."). If someone else changed it first, you are offered **Reload policy**.

#### TC-SET-07 – Email (SMTP) settings

**Requirement:** REQ-SET-06 · **Technique:** EP · **Priority:** H · **Result:** PASS

**Steps**

1. Open **Settings**, **Email**. Set **Provider** to **Other SMTP relay**.
2. Leave **Host** empty and save. Then enter a **Port** of 0 and of 70000.
3. Enter the real host, port, **Security**, **Relay username**, and **Relay password**. Save.
4. Reopen the tab and save again with the password box left blank.
5. Press **Test email** (save first).

**Expected result**

- An empty host and an invalid port are refused ("The port must be a whole number from 1 to 65535.").
- A saved password shows as "A password is saved. Leave this blank to keep it." and stays when the box is left blank.
- The test email reaches your own mailbox, and the server response shows.

#### TC-SET-08 – A failed save restores the old values

**Requirement:** REQ-SET-07 · **Technique:** ST · **Priority:** H · **Result:** PASS

**Steps**

1. On a lab appliance only, make the Nagios configuration invalid (for example, add a bad line to a copy that Nagios reads, and note how to undo it).
2. In **Settings**, **System** change the **Check interval** and press **Save Changes**.
3. Undo the break.

**Expected result**

- An error shows that the change could not be applied.
- The old value is back on screen and in effect.

#### TC-SET-09 – Maintenance Mode

**Requirement:** REQ-SET-07 · **Technique:** EG · **Priority:** M · **Result:** PASS

**Steps**

1. In **Settings**, **System** find the **Maintenance** section and turn **Maintenance Mode** on. Save.
2. Open another page.
3. Click the link in the banner.
4. Turn Maintenance Mode off.

**Expected result**

- The banner "Maintenance mode is on." shows on every page and links to **Maintenance**.
- The banner says it pauses only Pinpoint's own jobs. Alerts are not silenced.

## Test cases: discovery, device extras, shell, and quality

### Module 18 – Network Discovery

**Summary of cases**

| TC | Case | Req | Tech | Pri | Result |
| --- | --- | --- | --- | --- | --- |
| TC-DSC-01 | First scan finds every target | DSC-01 | EP | H | PASS |
| TC-DSC-02 | Scan progress and final status | DSC-02 | ST | H | PASS |
| TC-DSC-03 | Cancel a scan | DSC-03 | ST | M | PASS |
| TC-DSC-04 | Rescan with no change | DSC-04 | EG | M | PASS |
| TC-DSC-05 | Discovery settings apply to the next scan | DSC-05 | BVA | H | PASS |
| TC-DSC-06 | Removing a network keeps device ownership | DSC-06 | ST | H | PASS |
| TC-DSC-07 | A port that is no longer seen | DSC-07 | ST | M | PASS |
| TC-DSC-08 | Scan needs the discovery permission | DSC-08 | DT | H | PASS |
| TC-DSC-09 | Rescan starts at once | DSC-09 | EG | L | PASS |

A scan starts from **Rescan Network** (on **Overview**, and on **Network Health** for users who may scan). Progress and a **Cancel** button show in the header bell. Discovery settings are in **Settings**, **Network Discovery** (**Networks & Ports**).

#### TC-DSC-01 – First scan finds every target

**Requirement:** REQ-DSC-01 · **Technique:** EP · **Priority:** H · **Result:** Not run

**Before you start:** a subnet with 5 known target machines that are on, and the subnet listed under **Networks** in **Settings**, **Network Discovery**.

**Steps**

1. On **Overview** press **Rescan Network**.
2. Wait until the button stops saying "Scanning…".
3. Open **Device Inventory** and read **Hostname**, **IP Address**, and **State**.
4. Open one host's drawer and read the hostname, IP, MAC, and OS.

**Expected result**

- All 5 targets are listed with their IP addresses and state Up.
- Each device shows hostname, IP, MAC, and OS where the device reports them.
- The appliance's own address is not listed as a target.

#### TC-DSC-02 – Scan progress and final status

**Requirement:** REQ-DSC-02 · **Technique:** ST · **Priority:** H · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-19-module-18-discovery/REPORT.md)

**Steps**

1. Press **Rescan Network**. Read the button and the header bell.
2. Open `/api/system/discover/status` in a second tab every 5 seconds until it stops changing.

**Expected result**

- The button reads "Scanning… N%" and is disabled while the scan runs. The bell shows "Network scan in progress" and later "Network scan complete".
- The status goes from running to exactly one of Success, Failed, or Interrupted.

#### TC-DSC-03 – Cancel a scan

**Requirement:** REQ-DSC-03 · **Technique:** ST · **Priority:** M · **Result:** Not run

**Steps**

1. Press **Rescan Network**.
2. At once open the header bell and press **Cancel** on the scan item.
3. Open **System Logs**, tab **Network Discovery**.

**Expected result**

- The item says "Cancelling network scan…" and then "Network scan cancelled".
- The status is Interrupted and the log says the scan was cancelled.

#### TC-DSC-04 – Rescan with no change

**Requirement:** REQ-DSC-04 · **Technique:** EG · **Priority:** M · **Result:** Not run

**Steps**

1. Run a rescan and wait for it to finish.
2. Run another rescan without changing anything in the lab.
3. Open **System Logs**, **Network Discovery**.

**Expected result**

- The log says the host configuration is unchanged and Nagios was not reloaded.
- No device or port records change.

#### TC-DSC-05 – Discovery settings apply to the next scan

**Requirement:** REQ-DSC-05 · **Technique:** BVA · **Priority:** H · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-19-module-18-discovery/REPORT.md)

**Before you start:** a host that serves HTTP on port 8080, and `settings.discovery`.

**Steps**

1. In **Settings**, **Network Discovery** set the TCP ports to `1-1024` and save. (The default range already includes 8080, so adding it alone proves nothing.) Run a rescan.
2. Add `8080` to the ports and save. Run a rescan.
3. Try to save a port of `0`, `65536`, and `abc`.
4. Open **System Logs**, **Configuration Change**.
5. Put the original ports back.

**Expected result**

- After the first scan port 8080 is not found. After the second it is.
- Invalid ports are refused ("Port must be a number from 1 to 65535.").
- The Configuration Change log records each edit.

#### TC-DSC-06 – Removing a network keeps device ownership

**Requirement:** REQ-DSC-06 · **Technique:** ST · **Priority:** H · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-19-module-18-discovery/REPORT.md)

**Before you start:** two networks in the settings and devices found in both.

**Steps**

1. In **Settings**, **Network Discovery** remove one network and save.
2. Run a rescan.
3. Open **Device Inventory** and read the **Monitoring** column for devices of both networks.

**Expected result**

- Devices of the removed network stay as they were (or become Missing). They are not reassigned to a host of the scanned network.
- Devices of the scanned network do not become "Address unknown" because of the removal.

#### TC-DSC-07 – A port that is no longer seen

**Requirement:** REQ-DSC-07 · **Technique:** ST · **Priority:** M · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-19-module-18-discovery/REPORT.md)

**Steps**

1. Stop a monitored service on a target (for example SSH on the web VM).
2. Run a rescan, then open that device's **Ports**.
3. Run one more rescan and read the port again.

**Expected result**

- The port shows **Missing** with "Not seen lately", and its Nagios service stays.
- One missed scan does not delete or archive it.

#### TC-DSC-08 – Scan needs the discovery permission

**Requirement:** REQ-DSC-08 · **Technique:** DT · **Priority:** H · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-19-module-18-discovery/REPORT.md)

**Steps**

1. Sign in as a user without `system.discover` who can open **Network Health**.
2. Look at the **Rescan Network** button there and read its tooltip.
3. Open `/api/system/discover/status` in the address bar.
4. As Super Admin press **Rescan Network**, then cancel the scan from the bell.

**Expected result**

- The button is disabled with the tooltip "Your role can't run network scans", and the status API returns 403.
- Super Admin can start and cancel a scan.
- Note: the status file lists the Stop route as using a different permission. The code on `main` uses `system.discover` for both, so that row of the status file is out of date.

#### TC-DSC-09 – Rescan starts at once

**Requirement:** REQ-DSC-09 · **Technique:** EG · **Priority:** L · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-19-module-18-discovery/REPORT.md)

**Steps**

1. Press **Rescan Network** and watch for a confirmation dialog.
2. While it runs, try to press the button again.

**Expected result**

- The scan starts at once with no confirmation dialog.
- The button is disabled while scanning.
- Note (spec gap): the journey plan expects a confirmation modal. The app does not ask.

### Module 19 – Device Inventory extras (check options, SNMP, interfaces, alert recipients)

**Summary of cases**

| TC | Case | Req | Tech | Pri | Result |
| --- | --- | --- | --- | --- | --- |
| TC-DX-01 | Check options only on web and mail ports | DX-01 | DT | M | PASS |
| TC-DX-02 | Status code boundaries | DX-02 | BVA | H | PASS |
| TC-DX-03 | Save and reset check options | DX-03 | ST | H | PASS |
| TC-DX-04 | Check options are read-only without edit permission | DX-04 | DT | M | PASS |
| TC-DX-05 | Fields depend on the service | DX-02 | EP | L | PASS |
| TC-DX-06 | SNMP section | DX-05 | DT | H | FAIL |
| TC-DX-07 | Interfaces section | DX-06 | DT | M | PASS |
| TC-DX-08 | Who sees the alert recipients | DX-07 | DT | M | Not run |
| TC-DX-09 | Default recipients and ineligible users | DX-07 | EG | M | Not run |
| TC-DX-10 | A failed apply keeps the old choice | DX-07 | EG | M | Not run |

#### TC-DX-01 – Check options only on web and mail ports

**Requirement:** REQ-DX-01 · **Technique:** DT · **Priority:** M · **Result:** Not run

**Steps**

1. Open a device drawer and read **Ports**.
2. Look for **Check options** on: a Monitored `http` port, a Missing `imap` port, a Monitored `ssh` port, and a Suggested `http` port.

**Expected result**

- **Check options** shows only on the Monitored `http` port and the Missing `imap` port.

#### TC-DX-02 – Status code boundaries

**Requirement:** REQ-DX-02 · **Technique:** BVA · **Priority:** H · **Result:** Not run

**Steps**

1. Press **Check options** on a Monitored `http` port. The dialog is titled "Check options: http on {host}".
2. In **Expected status codes** type `99`, then `100`, then `200,301`, then `599`, then `600`, then `abc`.

**Expected result**

- `100`, `200,301`, and `599` are accepted.
- `99`, `600`, and `abc` are blocked with a message before anything is sent.

#### TC-DX-03 – Save and reset check options

**Requirement:** REQ-DX-03 · **Technique:** ST · **Priority:** H · **Result:** Not run

**Steps**

1. In the dialog type **Expected text** `Welcome` and a **Virtual host** `www.example.com`. Press **Save**.
2. Close and reopen the dialog, then reload the page and reopen it again.
3. Press **Reset to defaults**.

**Expected result**

- "Check options saved." shows and the values are there again after reopening and reloading.
- The Nagios config is applied for each save.
- **Reset to defaults** shows "Check options reset to the defaults." and is disabled while nothing is saved.

#### TC-DX-04 – Check options are read-only without edit permission

**Requirement:** REQ-DX-04 · **Technique:** DT · **Priority:** M · **Result:** Not run

**Steps**

1. As a user with `system.hosts` but not `system.hosts.edit`, open **Check options** on a Monitored `http` port.
2. Open it on a retired device as Super Admin.

**Expected result**

- The fields are disabled, **Save** and **Reset to defaults** are hidden, the dialog says "You can view the options but not change them.", and the button reads **Close**.

#### TC-DX-05 – Fields depend on the service

**Requirement:** REQ-DX-02 · **Technique:** EP · **Priority:** L · **Result:** Not run

**Steps**

1. Open **Check options** on an `https` port and open the **Request method** list.
2. Open it on a `pop3` port.

**Expected result**

- `https` shows **Expected text**, **Expected status codes**, **Virtual host**, and **Request method** (Default, GET, HEAD, POST, PUT, DELETE, OPTIONS, PATCH).
- `pop3` shows only **Expected greeting**, with its default shown.

#### TC-DX-06 – SNMP section

**Requirement:** REQ-DX-05 · **Technique:** DT · **Priority:** H · **Result:** FAIL (messages accurate; SNMP section disappears after Save, Test and Reset until refresh; [#244](https://github.com/esfen14/Pinpoint/issues/244))

**Recorded run:** [report](../test-runs/2026-10-19-module-19-device-extras/REPORT.md)

**Before you start:** a device with SNMP monitored.

**Steps**

1. In the device drawer find **SNMP** and open **SNMP version**. Choose **Version 1**, **Version 2c**, and **Version 3 (user and passwords)** in turn.
2. For Version 3 leave **SNMP v3 user** empty and save.
3. Save a password, reopen the section, then save again with the password box blank.
4. Press **Remove saved** on a saved password.
5. As a user without `system.hosts.edit` open the section and look for the **Test** button.

**Expected result**

- The fields shown follow the version and security level, and a missing required field is blocked.
- A saved password shows only as "Saved", and a blank box keeps it. **Remove saved** deletes it.
- Changing and testing need `system.hosts.edit`. A successful test shows "The device answered:".

#### TC-DX-07 – Interfaces section

**Requirement:** REQ-DX-06 · **Technique:** DT · **Priority:** M · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-19-module-19-device-extras/REPORT.md)

**Steps**

1. Open the drawer of a device with SNMP and of one without.
2. On the SNMP device press **Refresh** in **Interfaces**.
3. Tick **Monitor** for one interface.

**Expected result**

- **Interfaces** shows only for the SNMP device, with name, index, speed, and status for each interface.
- Refresh reads the list from the device. The tick is saved and the interface then appears in **Interface Bandwidth** on Network Health.

#### TC-DX-08 – Who sees the alert recipients

**Requirement:** REQ-DX-07 · **Technique:** DT · **Priority:** M · **Result:** Not run

**Steps**

1. Open a discovered host's drawer as a user with `system.hosts.alerts`, then as one without.
2. Open `localhost` and a service view of a discovered host as the first user.

**Expected result**

- **Email alert recipients** shows only with `system.hosts.alerts` and only for a discovered host's host view.
- It does not show for `localhost` or in a service view.

#### TC-DX-09 – Default recipients and ineligible users

**Requirement:** REQ-DX-07 · **Technique:** EG · **Priority:** M · **Result:** Not run

**Steps**

1. In **Email alert recipients** save with no one ticked.
2. Tick one user whose account is Inactive (or has email alerts off) and save.

**Expected result**

- With none ticked the text says "Using the default recipients: all active accounts with email alerts on."
- The Inactive user is labelled "Inactive or email alerts off; this account will not receive alerts." With only that user ticked, the default recipients are used.

#### TC-DX-10 – A failed apply keeps the old choice

**Requirement:** REQ-DX-07 · **Technique:** EG · **Priority:** M · **Result:** Not run

**Steps**

1. Tick a user and press **Save recipients** while the Nagios apply fails (lab only).

**Expected result**

- The old saved choice stays, the server's error shows, and your new ticks remain so you can retry.

### Module 20 – Settings extras and the application shell

**Summary of cases**

| TC | Case | Req | Tech | Pri | Result |
| --- | --- | --- | --- | --- | --- |
| TC-SHL-01 | Create an escalation | SHL-01 | EP | M | PASS |
| TC-SHL-02 | Invalid escalations are refused | SHL-02 | DT | H | PASS |
| TC-SHL-03 | Delete an escalation | SHL-03 | ST | M | PASS |
| TC-SHL-04 | The strong-password policy | SHL-04 | DT | H | PASS |
| TC-SHL-05 | Appliance storage card | SHL-05 | EG | M | PASS |
| TC-SHL-06 | Storage card permission | SHL-05 | DT | L | PASS |
| TC-SHL-07 | Notification bell | SHL-06 | ST | M | PASS |
| TC-SHL-08 | "Show notification bell in the header" | SHL-07 | DT | M | PASS |
| TC-SHL-09 | Password request in the bell | SHL-08 | EP | M | PASS |
| TC-SHL-10 | Sidebar follows permissions | SHL-09 | DT | H | PASS |

#### TC-SHL-01 – Create an escalation

**Requirement:** REQ-SHL-01 · **Technique:** EP · **Priority:** M · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-19-module-20-21-records/REPORT.md)

**Steps**

1. In **Settings**, **System** find **Escalations** and press **Add escalation**.
2. Choose a **Contact group** that has eligible members. Set **First notification** 2, **Last notification** 5, **Interval (minutes)** 30, and **Scope** "All hosts and services".
3. Press **Save escalation**.

**Expected result**

- "Escalation saved." shows, the escalation is listed as Active, and it is applied to Nagios.

#### TC-SHL-02 – Invalid escalations are refused

**Requirement:** REQ-SHL-02 · **Technique:** DT · **Priority:** H · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-19-module-20-21-records/REPORT.md)

**Steps**

1. Try to save with no **Contact group** chosen.
2. Try **First notification** 5 with **Last notification** 2.
3. Try **Interval (minutes)** 1441 and **First notification** 0.
4. Save a valid escalation while Nagios rejects it (lab only).

**Expected result**

- Each bad entry is refused with its message (for example "First notification must not exceed last notification.", "Interval must be an integer from 0 to 1440 minutes.").
- A Nagios rejection (422) shows an error and the change is rolled back.

#### TC-SHL-03 – Delete an escalation

**Requirement:** REQ-SHL-03 · **Technique:** ST · **Priority:** M · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-19-module-20-21-records/REPORT.md)

**Steps**

1. Press **Delete** on an escalation and **Cancel deletion**.
2. Press **Delete** again and **Confirm deletion**.
3. Repeat while the Nagios apply fails (lab only).

**Expected result**

- Cancel keeps it. Confirming removes it ("Escalation deleted.") and applies the change.
- When the apply fails the escalation is restored and an error shows.

#### TC-SHL-04 – The strong-password policy

**Requirement:** REQ-SHL-04 · **Technique:** DT · **Priority:** H · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-19-module-20-21-records/REPORT.md)

**Steps**

1. In **Settings**, **Security** set "Require stronger passwords for accounts" to **Enabled** and save.
2. In **Manage Accounts** press **+ Add User** and type `Weakpass1` in both password boxes.
3. Type `Lab-Pinpoint-2026!` instead.
4. Set the policy to **Disabled**, save, and try `Weakpass1` again.

**Expected result**

- With the policy on, the hint reads "Passwords need 12+ characters with upper, lower, a number, and a symbol.", `Weakpass1` cannot be saved, and the compliant password can.
- With the policy off, 8 or more characters are enough ("Passwords need at least 8 characters.").

#### TC-SHL-05 – Appliance storage card

**Requirement:** REQ-SHL-05 · **Technique:** EG · **Priority:** M · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-19-module-20-21-records/REPORT.md)

**Steps**

1. Open **Overview** and read **Appliance storage**.
2. On a lab where a storage location has less than 10% free space, read it again.
3. Make one location unmeasurable (rename its folder in the lab) and reload.

**Expected result**

- The card shows the size of each database, **Database backups**, and **Nagios archives**, plus free disk space.
- Below 10% free it warns "Low disk space: a storage location is below 10% free. Review backups and log retention."
- An unmeasurable location shows "Unavailable", and a partial folder scan shows "At least".

#### TC-SHL-06 – Storage card permission

**Requirement:** REQ-SHL-05 · **Technique:** DT · **Priority:** L · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-19-module-20-21-records/REPORT.md)

**Steps**

1. Sign in as the dashboard-only user and open **Overview**.
2. Sign in as the Staff user and type `/dashboard`.

**Expected result**

- The dashboard-only user sees **Appliance storage**.
- The Staff user cannot open the Dashboard at all.

#### TC-SHL-07 – Notification bell

**Requirement:** REQ-SHL-06 · **Technique:** ST · **Priority:** M · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-19-module-20-21-records/REPORT.md)

**Steps**

1. Cause a notification (finish a **Rescan Network**).
2. Read the unread count on the bell, then open it.
3. Press **Mark all read**, then reload the page.
4. Press **Clear**.

**Expected result**

- The unread count matches the number of new items in the panel.
- After **Mark all read** the count is 0 and stays 0 after a reload.
- **Clear** empties the list ("No notifications").

#### TC-SHL-08 – "Show notification bell in the header"

**Requirement:** REQ-SHL-07 · **Technique:** DT · **Priority:** M · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-19-module-20-21-records/REPORT.md)

**Steps**

1. In **Settings**, **General Settings** untick **Show notification bell in the header** and save.
2. Cause a Critical alert and look at your mailbox.
3. Tick the box again and save.

**Expected result**

- The bell disappears from the header.
- The alert email is still sent, because the toggle only shows or hides the bell.

#### TC-SHL-09 – Password request in the bell

**Requirement:** REQ-SHL-08 · **Technique:** EP · **Priority:** M · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-19-module-20-21-records/REPORT.md)

**Steps**

1. On `/login` submit **Forgot Password?** for a registered user.
2. Sign in as Super Admin and open the bell.
3. Open **Manage Accounts** and the **Password reset requests** panel.

**Expected result**

- The bell shows a pending password request, and the same request is in the panel.

#### TC-SHL-10 – Sidebar follows permissions

**Requirement:** REQ-SHL-09 · **Technique:** DT · **Priority:** H · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-19-module-20-21-records/REPORT.md)

**Steps**

1. Create a role with only `system.history` and a user with it. Sign in as that user.
2. Read the sidebar and type `/reports` in the address bar.

**Expected result**

- The sidebar shows **History** (and **Settings**) only.
- `/reports` redirects to **History**, the first page the user may use.

### Module 21 – Security and quality

**Summary of cases**

| TC | Case | Req | Tech | Pri | Result |
| --- | --- | --- | --- | --- | --- |
| TC-NFR-01 | API needs a session | NFR-01 | DT | H | PASS |
| TC-NFR-02 | An ended session is refused | NFR-01 | EG | H | PASS |
| TC-NFR-03 | Script and SQL characters are plain text | NFR-02 | EG | H | PASS |
| TC-NFR-04 | Light and dark mode | NFR-03 | EP | L | PASS |
| TC-NFR-05 | Narrow width | NFR-03 | BVA | L | PASS |
| TC-NFR-06 | Failure shows an error with Retry | NFR-04 | EG | H | FAIL |
| TC-NFR-07 | Start-up time | NFR-05 | BVA | M | FAIL - returns to login, other result is, data is showing but plaintext only without UI |
| TC-NFR-08 | Availability for 10 hosts | NFR-06 | BVA | M | FAIL - returns to login, other result is, data is showing but plaintext only without UI |
| TC-NFR-09 | Dashboard refresh time | NFR-07 | BVA | M | PASS |
| TC-NFR-10 | An alert appears quickly | NFR-08 | BVA | M | PASS |
| TC-NFR-11 | Four-hour stability run | NFR-09 | ST | L | PASS |

#### TC-NFR-01 – API needs a session

**Requirement:** REQ-NFR-01 · **Technique:** DT · **Priority:** H · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-19-module-20-21-records/REPORT.md)

**Steps**

1. Sign out (or open a private window with no login).
2. Open each of these in the address bar: `/api/system/dashboard/summary`, `/api/system/log`, `/api/user/accounts`, `/api/system/report/availability`, `/api/system/history/alerts`, `/api/system/network-health/hosts`.

**Expected result**

- Each returns 401 and no data.

#### TC-NFR-02 – An ended session is refused

**Requirement:** REQ-NFR-01 · **Technique:** EG · **Priority:** H · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-19-module-20-21-records/REPORT.md)

**Steps**

1. Sign in, then delete the session cookie in the browser's developer tools.
2. Click any sidebar link.
3. Sign in again, sign out in a second tab, and click any link in the first tab.

**Expected result**

- The next request returns 401 and the page goes to `/login`.

#### TC-NFR-03 – Script and SQL characters are plain text

**Requirement:** REQ-NFR-02 · **Technique:** EG · **Priority:** H · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-19-module-20-21-records/REPORT.md)

**Steps**

1. Create a role named `<script>alert(1)</script>` in **Manage Roles**.
2. In **Search hostname** on **Device Inventory** and in a **History** host filter type `' OR 1=1 --`.

**Expected result**

- The role name shows as plain text and no alert box appears.
- The searches return no rows or normal results, with no error and no extra data.

#### TC-NFR-04 – Light and dark mode

**Requirement:** REQ-NFR-03 · **Technique:** EP · **Priority:** L · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-19-module-20-21-records/REPORT.md)

**Steps**

1. In **Settings**, **General Settings** set **Theme** to light, then dark.
2. Visit every page in each theme.

**Expected result**

- Text is readable and the state colors (green, amber, red) can be told apart in both themes.

#### TC-NFR-05 – Narrow width

**Requirement:** REQ-NFR-03 · **Technique:** BVA · **Priority:** L · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-19-module-20-21-records/REPORT.md)

**Steps**

1. Set the browser width to 375 px (developer tools, device mode).
2. Open **Overview**, **Device Inventory** with a host drawer open, and **Ports**.

**Expected result**

- No page needs sideways scrolling, and the drawers and their buttons stay usable.

#### TC-NFR-06 – Failure shows an error with Retry

**Requirement:** REQ-NFR-04 · **Technique:** EG · **Priority:** H · **Result:** FAIL (Overview shows its load error with no Retry button; [#245](https://github.com/esfen14/Pinpoint/issues/245))

**Recorded run:** [report](../test-runs/2026-10-19-module-20-21-records/REPORT.md)

**Steps**

1. On the appliance stop the Pinpoint service. Open **Overview**, a host drawer, and **Ports** (open them before you stop it, then press their reload or retry controls).
2. Start the service again and press **Retry**.

**Expected result**

- Each part shows an error message with **Retry** (for example "Unable to load dashboard data."), not a blank page.
- After the service is back, **Retry** loads the data.

#### TC-NFR-07 – Start-up time

**Requirement:** REQ-NFR-05 · **Technique:** BVA · **Priority:** M · **Result:** FAIL (initial run; later tester-reported retest PASS, no timings recorded)

**Recorded run:** [report](../test-runs/2026-10-19-module-20-21-records/REPORT.md)

**Finding:** [#220](https://github.com/esfen14/Pinpoint/issues/220) (open; asks to clarify the conflicting results)

**Steps**

1. On the appliance restart the Pinpoint service and start a stopwatch.
2. Sign in and call `/api/system/dashboard/summary` until it returns data. Stop the stopwatch.
3. Repeat 3 times.

**Expected result**

- The middle of the three times is 10 seconds or less.

#### TC-NFR-08 – Availability for 10 hosts

**Requirement:** REQ-NFR-06 · **Technique:** BVA · **Priority:** M · **Result:** FAIL (initial run; later tester-reported retest PASS, no timings recorded)

**Recorded run:** [report](../test-runs/2026-10-19-module-20-21-records/REPORT.md)

**Finding:** [#221](https://github.com/esfen14/Pinpoint/issues/221) (open; asks to clarify the conflicting results)

**Steps**

1. With 10 monitored hosts time `/api/system/network-health/availability` and `/api/system/report/availability` 10 times each (use the browser's network panel).

**Expected result**

- 9 or more of the 10 responses for each are 5 seconds or less.

#### TC-NFR-09 – Dashboard refresh time

**Requirement:** REQ-NFR-07 · **Technique:** BVA · **Priority:** M · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-19-module-20-21-records/REPORT.md)

**Steps**

1. With at least 15 hosts and services reporting, open **Overview** and the browser's network panel.
2. Reload the page 5 times and note the time from the reload to the last data request finishing.

**Expected result**

- The middle of the five times is 3 seconds or less.

#### TC-NFR-10 – An alert appears quickly

**Requirement:** REQ-NFR-08 · **Technique:** BVA · **Priority:** M · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-19-module-20-21-records/REPORT.md)

**Steps**

1. Break a target host. Note the time Nagios records the state change (its web page or log).
2. Watch `/api/system/dashboard/alerts` (reload every second) and note when the alert appears.
3. Fix the host and repeat once.

**Expected result**

- The alert appears within 3 seconds of the Nagios state change in both runs. If Pinpoint polls only every 60 seconds, a longer delay is a finding. Write down the numbers.

#### TC-NFR-11 – Four-hour stability run

**Requirement:** REQ-NFR-09 · **Technique:** ST · **Priority:** L · **Result:** PASS

**Recorded run:** [report](../test-runs/2026-10-19-module-20-21-records/REPORT.md)

**Steps**

1. Note the start time, the process numbers of Pinpoint and Nagios, and the free memory.
2. Every 5 minutes for 4 hours open `/api/user/me` and `/api/system/dashboard/summary`, and note free memory and any error in the Pinpoint log.
3. At the end note the same values again.

**Expected result**

- No restart of Pinpoint or Nagios, no error 500, the API answered at every sample, new status data arrived each hour, and free memory did not fall by more than 30% without recovering.

### Module 22 – Edge cases and robustness

**Historical result source:** PASS outcomes recorded in the previous module catalog (`Module_Blackbox_Test_Cases.md`, removed from the repo); detailed case results below are consolidated from its summary table.

These cases try the unusual: odd text, repeated clicks, lost connections, two people at once, time changes, and large amounts of data. Run them in phase 13, after the normal cases pass, because they reuse the accounts, scans, and devices made earlier. For each case "no error page" means no blank screen, no stack trace, and no HTTP 500.

**Summary of cases**

| TC | Case | Req | Tech | Pri | Result |
| --- | --- | --- | --- | --- | --- |
| TC-EDG-01 | Very long text in names | EDG-01 | BVA | M | PASS |
| TC-EDG-02 | Accents, emoji, and symbols in names | EDG-02 | EG | M | PASS |
| TC-EDG-03 | Blank and space-only values | EDG-03 | EG | H | PASS |
| TC-EDG-04 | Double click on Save | EDG-04 | EG | H | PASS |
| TC-EDG-05 | Back button and page refresh | EDG-05 | EG | M | PASS |
| TC-EDG-06 | Connection lost during a save | EDG-06 | EG | H | PASS |
| TC-EDG-07 | Session ends with a dialog open | EDG-07 | EG | H | PASS |
| TC-EDG-08 | Two administrators edit the same role | EDG-08 | EG | M | PASS |
| TC-EDG-09 | Repeating an action many times | EDG-09 | ST | M | PASS |
| TC-EDG-10 | Time zone change | EDG-10 | EP | M | PASS |
| TC-EDG-11 | A maintenance window across midnight | EDG-11 | BVA | L | PASS |
| TC-EDG-12 | Special characters in search boxes | EDG-12 | EG | M | PASS |
| TC-EDG-13 | Password length boundaries | EDG-13 | BVA | H | PASS |
| TC-EDG-14 | The same email in a different letter case | EDG-14 | EG | M | PASS |
| TC-EDG-15 | Port number and range boundaries | EDG-15 | BVA | M | PASS |
| TC-EDG-16 | Reload during a running scan | EDG-16 | ST | M | PASS |
| TC-EDG-17 | Large amounts of data | EDG-17 | BVA | L | PASS |
| TC-EDG-18 | Starting a second scan while one runs | EDG-18 | ST | M | PASS |

#### TC-EDG-01 – Very long text in names

**Requirement:** REQ-EDG-01 · **Technique:** BVA · **Priority:** M · **Result:** PASS

**Steps**

1. As Super Admin open **Manage Roles** and press **+ Add Role**.
2. Type a **Role Name** of 200 letters `a` and a description of 500 characters. Save.
3. Press **+ Add Role** again and type a **Role Name** of 1,000 letters `a`. Save.
4. Look at the roles list, then open each role you made.
5. Delete or rename the test roles afterwards.

**Expected result**

- Each save either works or is refused with a message that tells you the limit. There is no error page.
- A saved long name does not break the page layout (it wraps or is shortened with the full text available when you open the role).

#### TC-EDG-02 – Accents, emoji, and symbols in names

**Requirement:** REQ-EDG-02 · **Technique:** EG · **Priority:** M · **Result:** PASS

**Steps**

1. Press **+ Add User** and type **First Name** `José` and **Last Name** `Peña 🙂`. Use a new email and a compliant password. Save.
2. Press **+ Add User** again with **First Name** `O'Brien "QA"` and **Last Name** `Tom & Jerry <b>`. Save.
3. Look at both rows. Type part of each name in the **Search** box.
4. Press **Export** in **Manage Accounts** and open the file.

**Expected result**

- Both accounts are saved and shown exactly as typed, as plain text. No bold text, no cut-off at the `<` or `&`.
- Search finds them, and the exported file shows the same characters.

#### TC-EDG-03 – Blank and space-only values

**Requirement:** REQ-EDG-03 · **Technique:** EG · **Priority:** H · **Result:** PASS

**Steps**

1. Press **+ Add Role** and type three spaces in **Role Name**. Try to save.
2. On an active alert press **Acknowledge** and type three spaces as the comment. Look at the confirm button.
3. Press **New window** in **Maintenance** and type three spaces as the **Reason**. Try to create it.
4. Press **+ Add User** and type three spaces in **First Name**. Try to save.

**Expected result**

- All four are refused (the button stays disabled or a message shows). No record is created.
- A value with spaces around it, such as `abc`, is saved without the extra spaces or is shown the same way each time.

#### TC-EDG-04 – Double click on Save

**Requirement:** REQ-EDG-04 · **Technique:** EG · **Priority:** H · **Result:** PASS

**Steps**

1. Press **+ Add User**, fill the form with a new email, and double-click the save button.
2. Press **+ Add Role**, fill a new name, and double-click the save button.
3. In **Maintenance** fill a valid new window and double-click **Create window**.
4. Count the new rows in each list.

**Expected result**

- Exactly one account, one role, and one window are created.
- No duplicate row appears. A message about the second click (such as "Email already exists.") is acceptable, but there is no error page.

#### TC-EDG-05 – Back button and page refresh

**Requirement:** REQ-EDG-05 · **Technique:** EG · **Priority:** M · **Result:** PASS

**Steps**

1. Sign out through **Sign Out**. Press the browser's Back button several times.
2. Sign in, press **+ Add User**, type a few fields, and reload the page.
3. In **NCPA Deployment** open the deploy wizard at **Check logins** and reload the page.

**Expected result**

- After sign-out, Back shows the login page or a page with no data. No protected data appears.
- After the reload in step 2, the dialog is closed and no account was created.
- After the reload in step 3, the wizard starts again from the beginning and no deployment started.

#### TC-EDG-06 – Connection lost during a save

**Requirement:** REQ-EDG-06 · **Technique:** EG · **Priority:** H · **Result:** PASS

**Steps**

1. Press **+ Add Role**, type a new name, and tick one permission.
2. In the browser's developer tools (Network tab) set the connection to **Offline**.
3. Press save and read the message.
4. Set the connection back to **Online** and press save again.
5. In **Settings**, **General Settings** repeat steps 2 to 4 with a changed **Theme** and **Save Changes**.

**Expected result**

- While offline the page shows an error (for example "Unable to create the role."), the dialog stays open with your entries, and nothing is saved.
- After going online, the second save works once. There is no duplicate role.
- The Settings change is saved only after the second try, and the old value is not shown as saved while offline.

#### TC-EDG-07 – Session ends with a dialog open

**Requirement:** REQ-EDG-07 · **Technique:** EG · **Priority:** H · **Result:** PASS

**Steps**

1. Sign in, press **+ Add User**, and fill every field with a new email.
2. In the browser's developer tools delete the session cookie (Application, Cookies).
3. Press save.
4. Sign in again and look for the new account.

**Expected result**

- The save is refused (401). The page goes to `/login` or shows an error, and no stack trace shows.
- After signing in again the new account does not exist.

#### TC-EDG-08 – Two administrators edit the same role

**Requirement:** REQ-EDG-08 · **Technique:** EG · **Priority:** M · **Result:** PASS

**Steps**

1. In browser A and in a private window B, sign in as Super Admin and open the same non-built-in role in **Edit Role**.
2. In A change the description and save.
3. In B change the permissions (tick one more) and save.
4. Reload the role in both windows.

**Expected result**

- Both saves finish with no error page.
- The role ends in one consistent state, not a mix that neither person chose. Write down which edit won.
- If B's save silently erased A's description with no warning, report it as a finding (a lost update).

#### TC-EDG-09 – Repeating an action many times

**Requirement:** REQ-EDG-09 · **Technique:** ST · **Priority:** M · **Result:** PASS

**Steps**

1. On one active alert press **Acknowledge** (with a comment) and **Unacknowledge**, 10 times each in turn.
2. In a host drawer press **Pause monitoring** (confirm) and **Resume monitoring** (confirm), 5 times each in turn.
3. Open **System Logs**, **Activity Log** and count the entries for those actions.

**Expected result**

- After each action the alert and the device show the state of the last action, and no button stays stuck on "Saving…".
- The Activity Log has one entry for each pause and resume (10 in total), and the acknowledgements are recorded in History in order.

#### TC-EDG-10 – Time zone change

**Requirement:** REQ-EDG-10 · **Technique:** EP · **Priority:** M · **Result:** PASS

**Steps**

1. In **Settings**, **General Settings** note the **Time Zone** setting. Open **History** and a **Maintenance** window and write down the time of one event and of the window.
2. Change **Time Zone** to a zone about 8 hours away from the first and press **Save Changes**.
3. Open the same History event and the same window.
4. Put the original **Time Zone** back.

**Expected result**

- Every time on screen moves by the difference between the two zones, in History, Maintenance, Reports, and System Logs.
- The order of the events does not change, and no time shows as invalid.

#### TC-EDG-11 – A maintenance window across midnight

**Requirement:** REQ-EDG-11 · **Technique:** BVA · **Priority:** L · **Result:** PASS

**Steps**

1. In **Maintenance** create a window that starts at 23:30 tomorrow and ends at 00:30 the day after, **Does not repeat**.
2. Create a second window with **Repeats** set to **Every day**, starting at 22:00 and ending at 23:00.
3. If you can set the lab's clock to the day before a daylight-saving change, read the next occurrence on both sides of the change.

**Expected result**

- The window across midnight is accepted and its next occurrence shows the right start and end days.
- The daily window keeps the same local time (22:00) on every occurrence, including across a daylight-saving change when the time zone is the browser's.

#### TC-EDG-12 – Special characters in search boxes

**Requirement:** REQ-EDG-12 · **Technique:** EG · **Priority:** M · **Result:** PASS

**Steps**

1. In **Search hostname** (Device Inventory), **Search host or service** (System Status), and **Search** (Manage Accounts) type, one at a time: `%`, `_`, `'`, `"`, `\`, `<script>`, a string of 500 letters, and three spaces.
2. Clear each box after each value.

**Expected result**

- No error page and no script runs.
- Results are consistent for each value (a literal match or no rows), and clearing the box brings the full list back.

#### TC-EDG-13 – Password length boundaries

**Requirement:** REQ-EDG-13 · **Technique:** BVA · **Priority:** H · **Result:** PASS

**Steps**

1. In **Settings**, **Security** set "Require stronger passwords for accounts" to **Enabled** and save.
2. In **Manage Accounts** press **+ Add User** and type `Lab-Pass1!x` (11 characters) in both password boxes. Then type `Lab-Pass1!xy` (12 characters).
3. Set the policy to **Disabled** and save. Type `Lab-1xy` (7 characters), then `Lab-1xyz` (8 characters).
4. Repeat one of the lengths in **Edit Account** (**NEW PASSWORD**) and in **Change your password**.

**Expected result**

- Policy on: 11 characters is refused with the 12-or-more rule, and 12 characters is accepted.
- Policy off: 7 characters is refused ("Passwords need at least 8 characters.") and 8 characters is accepted.
- The same limits apply in all three places.

#### TC-EDG-14 – The same email in a different letter case

**Requirement:** REQ-EDG-14 · **Technique:** EG · **Priority:** M · **Result:** PASS

**Steps**

1. Press **+ Add User** and create `Edge.Case@mail-lab.com`.
2. Press **+ Add User** again and try `edge.case@mail-lab.com`.
3. On `/login` sign in with `EDGE.CASE@mail-lab.com` and the password.

**Expected result**

- The second account is refused ("Email already exists.") because the same address in another letter case is a duplicate.
- Write down whether the login in step 3 works. It should either work or be refused with the normal message, and never show an error page.

#### TC-EDG-15 – Port number and range boundaries

**Requirement:** REQ-EDG-15 · **Technique:** BVA · **Priority:** M · **Result:** PASS

**Steps**

1. In **Settings**, **Network Discovery** open the TCP ports list.
2. Try to add these, one at a time: `0`, `1`, `65535`, `65536`, `-1`, `22,80`, `1-65535`, `100-10`, and an empty entry.
3. Press **Discard Changes** afterwards.

**Expected result**

- `1`, `65535`, and `1-65535` are accepted. `0`, `65536`, `-1`, and the empty entry are refused with "Enter a port (1-65535) or a range like 1-1024." or "Port must be a number from 1 to 65535."
- The reversed range `100-10` is refused with a message, and the entry `22,80` is either accepted as two ports or refused with a message, not accepted silently as one bad value.

#### TC-EDG-16 – Reload during a running scan

**Requirement:** REQ-EDG-16 · **Technique:** ST · **Priority:** M · **Result:** PASS

**Steps**

1. Press **Rescan Network** and wait until it shows "Scanning… N%".
2. Reload the page, then open another page and come back.
3. Open `/api/system/discover/status`.

**Expected result**

- After the reload the page still shows the scan running, and the **Rescan Network** button is disabled or says "Scanning…".
- Only one scan runs, and it finishes with exactly one final status.

#### TC-EDG-17 – Large amounts of data

**Requirement:** REQ-EDG-17 · **Technique:** BVA · **Priority:** L · **Result:** PASS

**Before you start:** a lab or a test database with at least 100 hosts, 500 services, and 5,000 History events.

**Steps**

1. Open **Device Inventory**, **System Status**, and **History**. Write down how long each takes to show data.
2. Go to the last page of each list, change **Rows per page** to 100, and search for a name that is near the end.
3. Run the **Host Availability** report for **Last 30 days** and export it as CSV.

**Expected result**

- Each page loads with no error page. Paging, sorting, search, and the export all work and give the right counts.
- Write down the load times. A page that takes more than 10 seconds, or freezes the browser, is a finding.

#### TC-EDG-18 – Starting a second scan while one runs

**Requirement:** REQ-EDG-18 · **Technique:** ST · **Priority:** M · **Result:** PASS

**Steps**

1. Press **Rescan Network** and try to press it again at once.
2. While the scan runs, open a second browser as Super Admin and press **Rescan Network** there.
3. Send a start request to `/api/system/discover/start` with a tool such as curl while the scan runs.

**Expected result**

- The button is disabled while scanning. The second browser and the API call are refused (400, "Network discovery is already running."), and only one scan runs.

### Module 23 – Order of events

**Historical result source:** PASS outcomes recorded in the previous module catalog (`Module_Blackbox_Test_Cases.md`, removed from the repo); detailed case results below are consolidated from its summary table.

These cases test what happens when things occur in an unusual order: a fix before a confirmation, a change while another job runs, or a permission taken away while the user is working. Each case says which event comes first. Run them in phase 14, one at a time, and restore the lab after each one (services running, devices monitored, no window or pause left over).

**Summary of cases**

| TC | Case | Req | Tech | Pri | Result |
| --- | --- | --- | --- | --- | --- |
| TC-SEQ-01 | Acknowledge after the service has recovered | SEQ-01 | ST | M | PASS |
| TC-SEQ-02 | Break, recover, and break again during the retries | SEQ-02 | ST | M | PASS |
| TC-SEQ-03 | A maintenance window starts while an alert is active | SEQ-03 | ST | H | PASS |
| TC-SEQ-04 | A window cancelled before it starts | SEQ-04 | ST | M | PASS |
| TC-SEQ-05 | A window edited while it is running | SEQ-05 | ST | M | PASS |
| TC-SEQ-06 | Pause during an alert, recover, then resume | SEQ-06 | ST | M | PASS |
| TC-SEQ-07 | Pause a device during a scan | SEQ-07 | ST | M | PASS |
| TC-SEQ-08 | Save discovery settings during a scan | SEQ-08 | ST | M | PASS |
| TC-SEQ-09 | Enable a plugin before the first scan | SEQ-09 | ST | M | PASS |
| TC-SEQ-10 | Disable and re-enable a plugin that is monitoring | SEQ-10 | ST | M | PASS |
| TC-SEQ-11 | Stop monitoring a port, then rescan | SEQ-11 | ST | M | PASS |
| TC-SEQ-12 | A role is deactivated while its user is signed in | SEQ-12 | ST | H | PASS |
| TC-SEQ-13 | A permission is removed while the user is on the page | SEQ-13 | ST | H | PASS |
| TC-SEQ-14 | A user is suspended while signed in | SEQ-14 | ST | H | PASS |
| TC-SEQ-15 | A password is reset while the user is signed in | SEQ-15 | ST | H | PASS |
| TC-SEQ-16 | The forced password change is interrupted | SEQ-16 | ST | M | PASS |
| TC-SEQ-17 | First-run setup is interrupted | SEQ-17 | ST | H | PASS |
| TC-SEQ-18 | Kill switch off, failure, then switch on | SEQ-18 | ST | H | PASS |
| TC-SEQ-19 | Cooldown and hourly limit in sequence | SEQ-19 | ST | M | PASS |
| TC-SEQ-20 | Maintenance Mode and downtime before a failure | SEQ-20 | ST | M | PASS |
| TC-SEQ-21 | Disable `check_ncpa` after a deployment | SEQ-21 | ST | M | PASS |
| TC-SEQ-22 | Clean up, then redeploy, then restart | SEQ-22 | ST | L | PASS |
| TC-SEQ-23 | The same event order on every page | SEQ-23 | ST | M | PASS |
| TC-SEQ-24 | Pinpoint restarts during a scan | SEQ-24 | ST | M | PASS |

#### TC-SEQ-01 – Acknowledge after the service has recovered

**Requirement:** REQ-SEQ-01 · **Technique:** ST · **Priority:** M · **Result:** PASS

**Before you start:** a monitored service on the web VM that you can stop and start.

**Steps**

1. Stop the service and wait until it is Critical (hard) in **Active Alerts**.
2. Press **Acknowledge** and leave the comment box open, with a comment typed.
3. Start the service again and wait until it shows OK in **System Status**.
4. Press the confirm button in the open dialog.
5. Reload **Overview** and open **History**, tab **Alerts**.

**Expected result**

- No acknowledgement is left on a service that is OK. Either the request is refused with a message, or it is cleared at the next poll.
- The service is not in **Active Alerts**, and History shows the recovery as the last event.

#### TC-SEQ-02 – Break, recover, and break again during the retries

**Requirement:** REQ-SEQ-02 · **Technique:** ST · **Priority:** M · **Result:** PASS

**Steps**

1. Stop a monitored service. As soon as it shows Critical as a soft state (before the retries are used up), start it again.
2. Stop it again and wait until it is Critical (hard).
3. Open **History**, tab **Alerts** and tab **Notifications**, and read the mailbox.

**Expected result**

- History lists the state changes in the order they happened, newest first, with soft and hard states marked.
- A notification is sent only for the hard Critical state, once. No notification is sent for the first soft state.
- **Active Alerts** and the Dashboard cards match the final state.

#### TC-SEQ-03 – A maintenance window starts while an alert is active

**Requirement:** REQ-SEQ-03 · **Technique:** ST · **Priority:** H · **Result:** PASS

**Before you start:** working email (TC-SET-07).

**Steps**

1. Stop a monitored service and wait for the notification email (hard Critical).
2. In **Maintenance** create a window for that device that starts in 15 minutes and ends in 1 hour.
3. Wait until the window is active and check the mailbox and the device.
4. Wait until the window ends on its own and check the mailbox again.

**Expected result**

- While the window is active the device shows the scheduled downtime indicator and no new notification email is sent.
- When the window ends and the service is still Critical, notifications resume.
- The window shows Completed.

#### TC-SEQ-04 – A window cancelled before it starts

**Requirement:** REQ-SEQ-04 · **Technique:** ST · **Priority:** M · **Result:** PASS

**Steps**

1. Create a window that starts in 30 minutes.
2. Cancel it (**Cancel**, **Yes, cancel it**).
3. Wait past the start time. Stop a service on that device.

**Expected result**

- The window shows Cancelled and never becomes Running.
- At the old start time the device does not show downtime, and the failure sends a notification.

#### TC-SEQ-05 – A window edited while it is running

**Requirement:** REQ-SEQ-05 · **Technique:** ST · **Priority:** M · **Result:** PASS

**Steps**

1. Create a window that is active now and ends in 1 hour. Check that the device shows downtime.
2. Press **Edit** and set **Ends** to 5 minutes from now. Press **Save changes**.
3. Wait until that time passes.

**Expected result**

- The device stays in downtime until the new end time and then leaves it. It does not stay in downtime for the old end time.
- The window list shows the new end.

#### TC-SEQ-06 – Pause during an alert, recover, then resume

**Requirement:** REQ-SEQ-06 · **Technique:** ST · **Priority:** M · **Result:** PASS

**Steps**

1. Stop a monitored service so it is Critical (hard).
2. In the host drawer press **Pause monitoring** and confirm.
3. Start the service again. Wait several minutes.
4. Press **Resume monitoring** and confirm. Wait one check interval.

**Expected result**

- While paused the host and its services are not counted and are not in **Active Alerts**.
- After resuming the device shows its current state (OK) and no stale alert appears.

#### TC-SEQ-07 – Pause a device during a scan

**Requirement:** REQ-SEQ-07 · **Technique:** ST · **Priority:** M · **Result:** PASS

**Steps**

1. Press **Rescan Network**.
2. While it runs, pause one device in **Device Inventory**.
3. Wait until the scan finishes and read the **Monitoring** column.

**Expected result**

- The pause is accepted and the scan finishes with no error.
- The device is still Paused after the scan.

#### TC-SEQ-08 – Save discovery settings during a scan

**Requirement:** REQ-SEQ-08 · **Technique:** ST · **Priority:** M · **Result:** PASS

**Steps**

1. Press **Rescan Network**.
2. Open **Settings**, **Network Discovery**, change a port, and try to save.
3. Wait until the scan ends and save again.

**Expected result**

- While the scan runs the page says "A network discovery scan is running. Changes can be saved once it finishes." and the save is blocked.
- After the scan ends the save works.

#### TC-SEQ-09 – Enable a plugin before the first scan

**Requirement:** REQ-SEQ-09 · **Technique:** ST · **Priority:** M · **Result:** PASS

**Before you start:** a fresh appliance where `check_http` is disabled and no scan has run.

**Steps**

1. In **Plugins** enable `check_http` first.
2. Then press **Rescan Network** and wait for it to finish.
3. Open the web VM's **Ports** and **System Status**.

**Expected result**

- Port 80 is Monitored without pressing **Monitor**, and the HTTP service shows in **System Status**.
- The final state is the same as when you scan first and enable the plugin second (E2E-02).

#### TC-SEQ-10 – Disable and re-enable a plugin that is monitoring

**Requirement:** REQ-SEQ-10 · **Technique:** ST · **Priority:** M · **Result:** PASS

**Steps**

1. With `check_http` monitoring the web VM, open the plugin and press **Disable**.
2. Open **System Status** and the web VM's **Ports**.
3. Press **Enable** again and **Confirm enable**. Look again.

**Expected result**

- After disabling, the HTTP services leave **System Status**. The port keeps its Monitored state and its reason says "{check\_plugin} is not enabled in Plugin Manager, so nothing is checking this port."
- After enabling, the services return and the reason is gone.

#### TC-SEQ-11 – Stop monitoring a port, then rescan

**Requirement:** REQ-SEQ-11 · **Technique:** ST · **Priority:** M · **Result:** PASS

**Steps**

1. On a Monitored port press **Stop monitoring** and confirm. The port moves to **Stopped**.
2. Press **Rescan Network** and wait for it to finish.
3. Look at the port again.

**Expected result**

- The scan does not turn the port back into Monitored. It stays in **Stopped** with "Monitoring stopped by an administrator."
- If it returns to Monitored on its own, report it as a finding.

#### TC-SEQ-12 – A role is deactivated while its user is signed in

**Requirement:** REQ-SEQ-12 · **Technique:** ST · **Priority:** H · **Result:** PASS

**Before you start:** the role `qa-view` and its user (TC-ROL-04).

**Steps**

1. In a private window sign in as that user and keep **Overview** open.
2. As Super Admin open **Manage Roles** and set `qa-view` to Inactive.
3. In the private window click a refresh control or reload the page.
4. As Super Admin set the role back to Active. Reload again in the private window.

**Expected result**

- After the role is Inactive its permissions stop working at once: the next request is refused (403) and the page shows an error or no data.
- After the role is Active again the user has the Dashboard back.

#### TC-SEQ-13 – A permission is removed while the user is on the page

**Requirement:** REQ-SEQ-13 · **Technique:** ST · **Priority:** H · **Result:** PASS

**Before you start:** a role with `system.dashboard` and `system.history` and a user with it.

**Steps**

1. In a private window sign in as that user and open **History**.
2. As Super Admin edit the role, untick `system.history`, and save.
3. In the private window press **Apply** on History, then reload the page.

**Expected result**

- The next History request returns 403 and no history data is shown.
- After the reload **History** is gone from the sidebar and `/history` redirects to the Dashboard. The Dashboard still works.

#### TC-SEQ-14 – A user is suspended while signed in

**Requirement:** REQ-SEQ-14 · **Technique:** ST · **Priority:** H · **Result:** PASS

**Steps**

1. Sign in as the Staff user in a private window.
2. As Super Admin set that user to Suspended and save.
3. In the private window click any link.
4. Try to sign in again. Then set the user to Active and sign in.

**Expected result**

- The next request signs the user out and shows `/login`.
- Sign-in is refused while Suspended and works again when Active.

#### TC-SEQ-15 – A password is reset while the user is signed in

**Requirement:** REQ-SEQ-15 · **Technique:** ST · **Priority:** H · **Result:** PASS

**Steps**

1. Sign in as the Staff user in a private window.
2. As Super Admin open that user's **Edit Account**, set a new password, and save.
3. In the private window click any link.
4. Try the old password, then the new one.

**Expected result**

- The open session ends on the next request.
- The old password fails. The new one works and forces a password change.

#### TC-SEQ-16 – The forced password change is interrupted

**Requirement:** REQ-SEQ-16 · **Technique:** ST · **Priority:** M · **Result:** PASS

**Steps**

1. Sign in as a user who must change the password. When "Change your password" shows, close the browser tab without changing it.
2. Open the app again and sign in with the same temporary password.
3. Change the password and sign out. Sign in with the temporary password once more.

**Expected result**

- The change-password window shows again at every sign-in until the password is changed.
- After the change, the temporary password no longer works.

#### TC-SEQ-17 – First-run setup is interrupted

**Requirement:** REQ-SEQ-17 · **Technique:** ST · **Priority:** H · **Result:** PASS

**Before you start:** a fresh install with the generated bootstrap login not yet set up.

**Steps**

1. Sign in with the bootstrap login. When "Finish setting up Pinpoint" shows, close the browser tab.
2. Open the app again and sign in with the same bootstrap login.
3. Open `/api/user/accounts`.
4. Finish the setup.

**Expected result**

- The setup window shows again, and nothing else can be used.
- `/api/user/accounts` returns 403 until setup is finished.
- After setup the bootstrap email and password stop working.

#### TC-SEQ-18 – Kill switch off, failure, then switch on

**Requirement:** REQ-SEQ-18 · **Technique:** ST · **Priority:** H · **Result:** PASS

**Before you start:** one enabled "Record only" action covering a service you can break.

**Steps**

1. In **Remediation** switch **Automatic recovery** off and confirm.
2. Break the service until it is a hard failure. Wait 2 minutes.
3. Switch **Automatic recovery** on and confirm. Wait 5 minutes without changing the service.
4. Open the **Run log**.

**Expected result**

- The failure that arrived while the switch was off is logged once as skipped by the kill switch.
- Switching on does not run the action for that old failure. Pinpoint does not queue it.
- A new failure after switching on does run.

#### TC-SEQ-19 – Cooldown and hourly limit in sequence

**Requirement:** REQ-SEQ-19 · **Technique:** ST · **Priority:** M · **Result:** PASS

**Before you start:** a "Record only" action with **Cooldown (seconds)** 60 and **Max runs per hour** 2.

**Steps**

1. Break the service (hard failure). Fix it.
2. Break it again within 60 seconds of the first failure. Fix it.
3. Wait over 60 seconds, then break it again. Fix it.
4. Wait over 60 seconds again, then break it a fourth time.
5. Read the **Run log** from oldest to newest.

**Expected result**

- Failure 1 is recorded as a run. Failure 2 is skipped because of the cooldown.
- Failure 3 is a run (the second of the hour).
- Failure 4 is skipped because of the hourly limit, even though the cooldown has passed.

#### TC-SEQ-20 – Maintenance Mode and downtime before a failure

**Requirement:** REQ-SEQ-20 · **Technique:** ST · **Priority:** M · **Result:** PASS

**Steps**

1. Turn **Maintenance Mode** on (Settings, System). Break a covered service to a hard failure. Fix it.
2. Turn **Maintenance Mode** off. Break it again to a hard failure.
3. Create a maintenance window that is active now for that device. Break the service again.
4. Read the **Run log**.

**Expected result**

- Step 1 is logged as skipped because of Maintenance Mode. Step 2 runs the action.
- Step 3 is logged as skipped because of the scheduled downtime.

#### TC-SEQ-21 – Disable `check_ncpa` after a deployment

**Requirement:** REQ-SEQ-21 · **Technique:** ST · **Priority:** M · **Result:** PASS

**Before you start:** a deployed NCPA device (TC-NCPA-04).

**Steps**

1. In **Plugins** disable `check_ncpa`. Open **NCPA Deployment** and **Overview**.
2. Enable `check_ncpa` again and wait two check intervals.

**Expected result**

- With the plugin disabled, NCPA services stop being monitored, **NCPA Deployment** shows its warning, and the resource data stops updating.
- After enabling, the NCPA services and data return without redeploying.

#### TC-SEQ-22 – Clean up, then redeploy, then restart

**Requirement:** REQ-SEQ-22 · **Technique:** ST · **Priority:** L · **Result:** PASS

**Before you start:** a deployed device with a saved **Remote restart** list and a remote-restart action (TC-NCPA-09, TC-REM-10).

**Steps**

1. Press **Clean up** on the device and run the cleanup.
2. Open **Remote restart** and read the list. Break the covered service to a hard failure and read the **Run log**.
3. Deploy NCPA again (TC-NCPA-02 to 04). Turn **Allow remote service restart** on and save.
4. Break the service again and read the **Run log**.

**Expected result**

- After Clean up the saved service list is still there, but the restart in step 2 does not succeed (it is logged as refused or failed).
- After redeploying and enabling, the restart in step 4 runs.

#### TC-SEQ-23 – The same event order on every page

**Requirement:** REQ-SEQ-23 · **Technique:** ST · **Priority:** M · **Result:** PASS

**Steps**

1. Break a service, wait for the hard failure and the email, acknowledge it, then fix it and wait for OK. Write down the time of each step.
2. Read the event order and times in: the **Active Alerts** table (**Since**), **History** tab **Alerts**, **History** tab **Notifications**, and **System Logs**, **Nagios log**.

**Expected result**

- Every page shows the same order: the failure, then the notification, then the acknowledgement, then the recovery.
- The times agree within one polling interval, and none shows a recovery before its failure.

#### TC-SEQ-24 – Pinpoint restarts during a scan

**Requirement:** REQ-SEQ-24 · **Technique:** ST · **Priority:** M · **Result:** PASS

**Steps**

1. Press **Rescan Network**.
2. While it runs, restart the Pinpoint service on the appliance.
3. Sign in again and open **Overview**. Open `/api/system/discover/status`.
4. Press **Rescan Network** once more.

**Expected result**

- The scan does not stay "Running" forever. It ends with a final status (Failed or Interrupted) within a few minutes.
- A new scan can then be started and finishes with Success.

## End-to-end scenarios

These eight scenarios run the whole system as a user would, from the browser and the lab's real machines, across several modules in one flow. They check only what the screen, the email, and the API show. Run them in order on a lab with: a fresh appliance, one web server VM (HTTP on port 80, SSH on port 22), a second Linux VM with SSH, an SMTP test mailbox, a Staff user, and a dashboard-only user. Default intervals apply (Check 5 minutes, Retry 1 minute, Maximum attempts 3). Record each step as PASS, FAIL, or PARTIALLY PASS in the Test Execution Log.

**Historical result source:** The prior catalog marks every step of E2E-01 through E2E-08 PASS (source: `Module_Blackbox_Test_Cases.md`, removed from the repo). No attributable test-run reports for these E2E results were found in `docs/test-runs/`.

### E2E-01 – First login to a working Dashboard

**Modules:** Authentication, Manage Accounts, Dashboard · **Priority:** H · **Result:** PASS (historical checklist)

| Step | What to do | What you should see |
| --- | --- | --- |
| 1 | Open the appliance address and sign in with the generated bootstrap login. | The window "Finish setting up Pinpoint" covers the page and cannot be closed. |
| 2 | Fill **Current password**, a **New email** on a non-reserved domain, and a compliant **New password** and **Confirm new password**. Press **Complete setup** and then **Continue**. | "Setup saved" shows and the Overview opens. |
| 3 | Sign out (confirm "Sign out of PinPoint?") and sign in with the new login. Then try the old bootstrap login. | The new login works. The old one is refused. |
| 4 | Read the Overview. | The four cards (**Total Hosts**, **Network Latency**, **Active Warnings**, **Critical Issues**) show, and sections without data say "No data" instead of staying empty. |

### E2E-02 – Discover the network and start monitoring a service

**Modules:** Settings, Device Inventory, Plugins, System Status, Dashboard · **Priority:** H · **Result:** PASS (historical checklist)

| Step | What to do | What you should see |
| --- | --- | --- |
| 1 | In **Settings**, **Network Discovery** check that the lab subnet is listed. On **Overview** press **Rescan Network**. | The button shows "Scanning… N%" and the bell shows "Network scan in progress", then "Network scan complete". |
| 2 | Open **Device Inventory**. | Both VMs are listed with their IP addresses. |
| 3 | Press **View host details** on the web VM and open **Ports**. Find port 80. | Port 80 is Suggested, and the reason says its plugin is not enabled. |
| 4 | Open **Plugins**, press `check_http`, press **Enable**, read the preview, and press **Confirm enable**. | The preview lists what will be monitored. The plugin becomes Enabled. |
| 5 | Return to the web VM's **Ports**. | Port 80 is now Monitored. |
| 6 | Open **System Status** and search the web VM. | An HTTP service for the web VM shows OK. |
| 7 | Open **Overview**. | **Total Hosts** includes the VMs, and the **Service Overview** counts match **System Status**. |

### E2E-03 – Deploy an NCPA agent and see its metrics

**Modules:** Plugins, NCPA Deployment, Network Health, Dashboard · **Priority:** H · **Result:** PASS (historical checklist)

| Step | What to do | What you should see |
| --- | --- | --- |
| 1 | Open **NCPA Deployment** while `check_ncpa` is disabled. | A warning says the agent's checks run only while `check_ncpa` is enabled. |
| 2 | Enable `check_ncpa` in **Plugins** and reopen the page. | The warning is gone. |
| 3 | Press **Verify** on the second VM, compare the fingerprint, and press **Trust**. Tick the VM and press **Deploy selected**. Enter a wrong SSH password, then the right one, and press **Check logins**. | The wrong password is rejected and nothing starts. The right one gives "Login and sudo verified." |
| 4 | Start the deployment and watch. | The run banner shows progress and ends with Success. |
| 5 | Open **Deployment History** and the run. | The run shows its steps, user, and time. No password appears anywhere. |
| 6 | Open **Overview** and **Network Health**. | **Average Resource Utilization** and CPU data appear for that host. |

### E2E-04 – Fault, alert, notification, acknowledgement, recovery, history

**Modules:** Dashboard, System Status, Alert acknowledgement, Settings (Email), History · **Priority:** H · **Result:** PASS (historical checklist)

| Step | What to do | What you should see |
| --- | --- | --- |
| 1 | In **Settings**, **Email** press **Test email**. | The email arrives in the mailbox. |
| 2 | On the web VM stop the web server service. Wait for the next check. | The HTTP service goes from OK to Critical, first as a soft state and then as a hard state after the maximum attempts. |
| 3 | Open **Overview**. | **Critical Issues** goes up by 1, and the **Active Alerts** table lists the HTTP service as Critical. |
| 4 | Check the mailbox. | One notification email arrives for the hard Critical state. |
| 5 | Press **Acknowledge** on the alert. Look at the confirm button with an empty comment, then type `Investigating` and confirm. | The button is disabled with an empty comment. After confirming the row shows acknowledged with your name. |
| 6 | Open **History**, tab **Notifications**. | The notification is listed and links to its alert. |
| 7 | Start the web server again and wait for the next check. | The service returns to OK and leaves **Active Alerts**. |
| 8 | Open **History**, tab **Alerts**, **Last hour**. | It lists the Critical event, the acknowledgement with your name, and the automatic resolved record, newest first. |

Timings to write down: failure time \_\_\_\_ · Critical (hard) shown \_\_\_\_ · email received \_\_\_\_ · recovery shown \_\_\_\_

### E2E-05 – A maintenance window silences alerts

**Modules:** Maintenance, Dashboard, Settings (Email), History · **Priority:** H · **Result:** PASS (historical checklist)

| Step | What to do | What you should see |
| --- | --- | --- |
| 1 | In **Maintenance** press **New window**. Choose the web VM, **Does not repeat**, **Starts** in 15 minutes, **Ends** in 1 hour, and a **Reason**. Press **Create window**. | "Maintenance window created." and the window is Scheduled. The Activity Log records it. |
| 2 | Wait until the window is active, then stop the web server. | The web VM shows the scheduled downtime indicator. |
| 3 | Wait past the check and retry time. Check the mailbox. | The service is Critical, but no email is sent for it. |
| 4 | Press **Cancel**, then **Keep it**. Press **Cancel** again and **Yes, cancel it**. | **Keep it** changes nothing. The second attempt sets the status to Cancelled. |
| 5 | Wait for the next check. | Alerts resume: an email arrives for the still-failing service. |
| 6 | Start the web server again. | The service returns to OK. |

### E2E-06 – Pause a device and see it leave the counts

**Modules:** Device Inventory, Dashboard, Network Health, Reports · **Priority:** M · **Result:** PASS (historical checklist)

| Step | What to do | What you should see |
| --- | --- | --- |
| 1 | Write down **Total Hosts** on the Overview. | Value noted. |
| 2 | In **Device Inventory** open the second VM, find **Monitoring**, press **Pause monitoring**. Cancel once, then confirm. | Cancel changes nothing. Confirming shows the chip Paused and "last known status". |
| 3 | Reload **Overview** and **Network Health**. | The host and its services leave **Total Hosts**, **Active Alerts**, and the online and offline cards. |
| 4 | Press **Rescan Network**. | The device stays Paused. |
| 5 | Press **Resume monitoring** and confirm. | The chip returns to Monitored and **Total Hosts** returns to the step 1 value after the next poll. |

### E2E-07 – A restricted user works only inside their role

**Modules:** Manage Roles, Manage Accounts, Authentication, Alert acknowledgement, System Logs · **Priority:** H · **Result:** PASS (historical checklist)

| Step | What to do | What you should see |
| --- | --- | --- |
| 1 | In **Manage Roles** press **+ Add Role**. Name it `qa-ack` and tick only `system.dashboard` and `system.acknowledge_alerts`. | The role is Active with exactly those two permissions. |
| 2 | In **Manage Accounts** press **+ Add User** with that role, status Active, and **Require password change at first sign-in** ticked. | The user is listed as Active. |
| 3 | Sign in as that user with the temporary password. | The window "Change your password" blocks until a compliant new password is saved. |
| 4 | Type each sidebar address in the address bar (see TC-ROL-04). | Only **Overview** (and **Settings**) open. The rest redirect to the Dashboard. |
| 5 | With an active alert, press **Acknowledge**, type a comment, and confirm. | It works and shows this user's name. |
| 6 | Open `/api/system/log` and `/api/user/accounts`. | Both return 403. |
| 7 | As Super Admin open **System Logs**, **Activity Log**, then set the user to Inactive and try to sign in as them. | The log shows the role and user creation, and the acknowledgement. Sign-in is refused. |

### E2E-08 – Report on the incident and check the export log

**Modules:** Reports, System Status, System Logs · **Priority:** M · **Result:** PASS (historical checklist)

| Step | What to do | What you should see |
| --- | --- | --- |
| 1 | After E2E-04 and E2E-05 open **Report**, tab **Host Availability**, **Last 24 hours**, **Run Report**. | The web VM's uptime is below 100% and every value is between 0 and 100. |
| 2 | Run the **Network Services** tab. | The HTTP service's OK, Warning, and Critical totals match **System Status** for the current state. |
| 3 | Press **Export** and choose CSV, then Excel, then PDF. | A `.csv` and an `.xls` download with the same rows as the table, and a print view opens for PDF. |
| 4 | Open **System Logs**, **Export Log**. | Three entries show: user, report type, format, period, and time. |
| 5 | Run the report for a **Custom range** before the install date. | An empty-state message shows with no error. |

### Requirements exercised by each end-to-end scenario

| Scenario | Requirements exercised |
| --- | --- |
| E2E-01 | REQ-AUTH-01, 03, 05; REQ-DASH-01, 06 |
| E2E-02 | REQ-DSC-01, 02; REQ-DI-02, 03, 11; REQ-PLG-03; REQ-SS-01; REQ-DASH-01, 04 |
| E2E-03 | REQ-NCPA-01, 02, 03, 05; REQ-PLG-03; REQ-DASH-06 |
| E2E-04 | REQ-DASH-03; REQ-SS-01; REQ-ACK-02, 06, 07; REQ-HIS-02, 04, 06; REQ-SET-06 |
| E2E-05 | REQ-MNT-02, 03, 06; REQ-HIS-02 |
| E2E-06 | REQ-DI-12, 13; REQ-DASH-02 |
| E2E-07 | REQ-ROL-01, 04; REQ-ACC-01, 02, 03; REQ-AUTH-04; REQ-ACK-01; REQ-LOG-01 |
| E2E-08 | REQ-RPT-01, 02, 03, 04, 05; REQ-LOG-01 |

## Requirements traceability matrix

All 193 requirements trace to at least one of the 231 test cases, and every test case traces to at least one requirement. **Source** abbreviations: **DR** `Display_Requirements.md`, **DIR** `Device_Inventory_Requirements.md`, **AHR** `Alerts_Notifications_History_Requirements.md`, **FMR** `Frontend_Modules_and_Routes.md`, **QA** `docs/qa/QA_Test_Plan.md` (journey case), **MAN** a file in `docs/manuals/`. "#" in a DIR source means its acceptance criterion number, and "(#123)" means the repository issue that added it. "App differs" means the real app does not follow the spec on that point, so the case tests the app and the difference is reported as a finding.

### Coverage summary

| Module | Requirements | Test cases | Covered |
| --- | --- | --- | --- |
| 1 Authentication | 8 | 12 | 100% |
| 2 Manage Accounts | 9 | 10 | 100% |
| 3 Manage Roles | 5 | 6 | 100% |
| 4 Dashboard | 8 | 9 | 100% |
| 5 Network Health | 7 | 7 | 100% |
| 6 System Status | 3 | 5 | 100% |
| 7 Alert acknowledgement | 7 | 8 | 100% |
| 8 History | 6 | 8 | 100% |
| 9 Device Inventory | 14 | 19 | 100% |
| 10 Topology | 3 | 6 | 100% |
| 11 Plugins | 6 | 7 | 100% |
| 12 NCPA Deployment | 8 | 11 | 100% |
| 13 Maintenance | 6 | 10 | 100% |
| 14 Remediation | 10 | 10 | 100% |
| 15 Reports | 6 | 7 | 100% |
| 16 System Logs | 4 | 5 | 100% |
| 17 Settings | 7 | 9 | 100% |
| 18 Network Discovery | 9 | 9 | 100% |
| 19 Device Inventory extras | 7 | 10 | 100% |
| 20 Settings extras and shell | 9 | 10 | 100% |
| 21 Security and quality | 9 | 11 | 100% |
| 22 Edge cases and robustness | 18 | 18 | 100% |
| 23 Order of events | 24 | 24 | 100% |
| **Total** | **193** | **231** | **100%** |

### Authentication, accounts, roles

| Req | Requirement | Source | Test cases |
| --- | --- | --- | --- |
| REQ-AUTH-01 | Valid credentials sign the user in and open the Dashboard | FMR, QA J1-03 | TC-AUTH-01 |
| REQ-AUTH-02 | A failed sign-in is refused with no session and does not reveal whether the email or password was wrong | QA J1-03 | TC-AUTH-02, 03, 04 |
| REQ-AUTH-03 | The bootstrap administrator must complete first-run setup (current password, new email, new password with confirmation) and cannot skip it | FMR, QA J1-07 | TC-AUTH-05, 06, 07 |
| REQ-AUTH-04 | A user flagged to change password is blocked until they do | FMR | TC-AUTH-08 |
| REQ-AUTH-05 | Sign out asks for confirmation | QA J1-05 | TC-AUTH-09 |
| REQ-AUTH-06 | An idle session ends after the configured Session Timeout (shortest option 15 minutes) | FMR | TC-AUTH-10 |
| REQ-AUTH-07 | Forgot Password sends the email to administrators, who set a new password | FMR | TC-AUTH-11 |
| REQ-AUTH-08 | `/` and unknown paths go to `/login`, and pages without access redirect | FMR | TC-AUTH-12 |
| REQ-ACC-01 | An administrator can add an account with a role and status, and the action is logged | FMR, QA J9-02 | TC-ACC-01, 02 |
| REQ-ACC-02 | "Require password change at first sign-in" is ticked by default and is honored | FMR | TC-ACC-03 |
| REQ-ACC-03 | Inactive and Suspended users cannot sign in | QA J9-05 | TC-ACC-04 |
| REQ-ACC-04 | Editing a signed-in user signs them out | QA J9-06 | TC-ACC-05 |
| REQ-ACC-05 | An administrator can reset another user's password in Edit Account, which forces a change | QA J9-07, FMR | TC-ACC-06 |
| REQ-ACC-06 | The bootstrap account stays Active and keeps an administration-capable role | FMR | TC-ACC-07 |
| REQ-ACC-07 | The email alerts option and column follow the `account.alerts` permission | FMR | TC-ACC-08 |
| REQ-ACC-08 | The accounts page needs `account.view` | FMR | TC-ACC-09 |
| REQ-ACC-09 | Add User selects the first active role by default and can create accounts one after another without a reload | FMR (#191) | TC-ACC-10 |
| REQ-ROL-01 | An administrator can create a role with chosen permissions, and it is logged | QA J9-01 | TC-ROL-01 |
| REQ-ROL-02 | The built-in Super Admin role is read-only and cannot be renamed | FMR (#112) | TC-ROL-02 |
| REQ-ROL-03 | The bootstrap administrator's role is locked against losing administration permissions | FMR | TC-ROL-03 |
| REQ-ROL-04 | Pages and APIs enforce role permissions (UI hides, URL redirects, API returns 403) | FMR, QA J9-04 | TC-ROL-04, 05 |
| REQ-ROL-05 | Settings tabs (Security, System, Network Discovery, Plugins, Email) each need their own `settings.*` permission | FMR | TC-ROL-06 |

### Monitoring views

| Req | Requirement | Source | Test cases |
| --- | --- | --- | --- |
| REQ-DASH-01 | Four summary cards: Total Hosts, Network Latency, Active Warnings, Critical Issues | DR §1.2, app differs | TC-DASH-01 |
| REQ-DASH-02 | Paused, retired, and merged devices and their services are left out of all counts | DR §1.2, DIR #34 | TC-DASH-02 |
| REQ-DASH-03 | The Active Alerts table lists every non-Up host and non-OK service, agrees with the cards, and shows an all-clear state | DR §1.6, §3.2 | TC-DASH-03, 04 |
| REQ-DASH-04 | The Service Overview panel shows service state counts that match System Status | DR §1.5 | TC-DASH-05 |
| REQ-DASH-05 | The header shows the refresh setting, and Service Overview warns when Nagios is not checking | DR §3.1, §3.4 | TC-DASH-06 |
| REQ-DASH-06 | Always-visible sections show "No data" and conditional NCPA sections hide | DR §3.2, §1.4 | TC-DASH-07 |
| REQ-DASH-07 | The Dashboard needs `system.dashboard` | FMR | TC-DASH-08 |
| REQ-DASH-08 | "Running out soon" shows disk and memory forecasts with a date and basis, and clear empty states | FMR (#156) | TC-DASH-09 |
| REQ-NH-01 | Network Health shows Online and Offline Devices that agree with the Dashboard | DR §2.1, FMR | TC-NH-01 |
| REQ-NH-02 | The host table (on Device Inventory) filters by state, acknowledgement, and monitoring, and searches by hostname | DR §2.2, FMR | TC-NH-02 |
| REQ-NH-03 | Host paging accepts `per_page` 1 to 100, default 25 | DR §2.2 | TC-NH-03 |
| REQ-NH-04 | Selecting a host opens a drawer (on Device Inventory) with performance data, timestamps, and its services | DR §2.2, FMR | TC-NH-04 |
| REQ-NH-05 | No average is shown with fewer than 2 data points | DR §3.5 | TC-NH-05 |
| REQ-NH-06 | Interface Bandwidth offers device, interface, and range choices and handles empty states | DR §2.5.1, FMR | TC-NH-06 |
| REQ-NH-07 | Flap history windows and Flapping only work (on Device Inventory) | FMR | TC-NH-07 |
| REQ-SS-01 | The service table shows state counts, search, filter, sort, and paging | FMR | TC-SS-01, 02, 03 |
| REQ-SS-02 | System Status needs `system.network_health` | FMR | TC-SS-04 |
| REQ-SS-03 | A service row shows a forecast badge, or "Not enough data yet" | FMR (#156) | TC-SS-05 |
| REQ-ACK-01 | Only users with Acknowledge Alerts see controls and can call the route | DR §4.2 | TC-ACK-02 |
| REQ-ACK-02 | Acknowledging needs a comment and records user and time | DR §4.4 | TC-ACK-01 |
| REQ-ACK-03 | Acknowledge all counts only unacknowledged alerts and takes one comment | DR §4.5 | TC-ACK-03, 04 |
| REQ-ACK-04 | Unacknowledge removes the acknowledgement without a comment (the spec also asks for a confirmation prompt, which the app does not show) | DR §4.6, app differs | TC-ACK-05 |
| REQ-ACK-05 | Acknowledgement filters exist (the spec asks for them on the alert list; the app has them in History) | DR §4.7, app differs | TC-ACK-06 |
| REQ-ACK-06 | Acknowledged rows show a muted badge with user and time and sort below others of equal severity | DR §4.8 | TC-ACK-07 |
| REQ-ACK-07 | A recovered alert is cleared automatically and recorded, and a repeat problem starts unacknowledged | DR §4.9 | TC-ACK-08 |
| REQ-HIS-01 | History needs its own permission, separate from Acknowledge Alerts | AHR §1 | TC-HIS-01 |
| REQ-HIS-02 | Filters: time preset, type, host, service, new state, acknowledged, state type, applied together | AHR §3.3 | TC-HIS-02, 03, 08 |
| REQ-HIS-03 | Date bounds must be a valid pair, and the default range is 24 hours | AHR §3.3 | TC-HIS-04 |
| REQ-HIS-04 | Default sort is newest first, and every column is sortable | AHR §3.4 | TC-HIS-05 |
| REQ-HIS-05 | Paging at 25, 50, or 100 with the total count shown | AHR §3.5 | TC-HIS-06 |
| REQ-HIS-06 | Rows expand, and alert and notification rows link to each other when they match | AHR §3.2, §5.4 | TC-HIS-07 |

### Device modules

| Req | Requirement | Source | Test cases |
| --- | --- | --- | --- |
| REQ-DI-01 | Ports show for a discovered device to users with `system.hosts` only | DIR #1 | TC-DI-01 |
| REQ-DI-02 | Ports are grouped and ordered as defined, with counts, and empty groups hidden | DIR §3, #2 | TC-DI-02 |
| REQ-DI-03 | Exactly one reason shows per port and the first match wins | DIR §4, #4 | TC-DI-03 |
| REQ-DI-04 | Without `system.hosts.edit` no action shows and a view-only note appears | DIR #5 | TC-DI-04 |
| REQ-DI-05 | Stop, Ignore, and Leave suggested ask for confirmation, and cancel changes nothing | DIR #7, #8 | TC-DI-05 |
| REQ-DI-06 | Stop monitoring and Resume move a port between Monitored, Ignored, and back | DIR §5 | TC-DI-05 |
| REQ-DI-07 | Leave suggested holds the port across scans and plugin toggles | DIR #12 | TC-DI-06 |
| REQ-DI-08 | Set service validates the name, shows the "Checked by" line, and disables Save when invalid | DIR §6, #13 | TC-DI-07, 08 |
| REQ-DI-09 | Pinning renames a monitored port's service, and Remove pin behaves as specified | DIR §6, #14, #21 to #23 | TC-DI-09 |
| REQ-DI-10 | The NCPA port of a deployed agent offers no destructive action | DIR #9 | TC-DI-10 |
| REQ-DI-11 | One monitoring label per device (first match wins), with a working Monitoring filter | DIR §12.1, #24 to #26 | TC-DI-11, 12 |
| REQ-DI-12 | Pause and Resume work, scans never undo a pause, and invalid transitions return 400 | DIR §12.3, #27 to #31 | TC-DI-13, 14 |
| REQ-DI-13 | The table opens on Monitored and shows "last known status" for out-of-config devices | DIR §12.2, #32, #33 | TC-DI-15 |
| REQ-DI-14 | Identity review lists unresolved issues and merging follows its safeguards | DIR §14 | TC-DI-16, 17, 18, 19 |
| REQ-TOP-01 | Topology shows every discovered device and the configured parent hierarchy, read-only | DIR §13 | TC-TOP-01, 02 |
| REQ-TOP-02 | Parent editing refuses self-links, duplicates, retired or merged parents, and cycles, keeps the draft, and warns about omitted parents | DIR §13 | TC-TOP-03, 04, 06 |
| REQ-TOP-03 | Only `system.hosts.edit` may change parents, and retired or merged devices are read-only | DIR §13 | TC-TOP-05 |

### Operations modules

| Req | Requirement | Source | Test cases |
| --- | --- | --- | --- |
| REQ-PLG-01 | Inventory shows category tabs and no Currently Running tab | FMR | TC-PLG-01 |
| REQ-PLG-02 | A banner shows while no plugin is enabled | FMR | TC-PLG-02 |
| REQ-PLG-03 | Enabling a plugin shows a preview and needs confirmation | FMR | TC-PLG-03 |
| REQ-PLG-04 | A plugin's monitored services can be searched, stopped, and resumed per device | FMR | TC-PLG-04 |
| REQ-PLG-05 | Custom checks show only with `plugin.custom_check` for supporting plugins, and passwords are masked and write-only | FMR | TC-PLG-05, 06 |
| REQ-PLG-06 | Plugins need `plugin.view` | FMR | TC-PLG-07 |
| REQ-NCPA-01 | A warning shows when `check_ncpa` is not enabled | FMR | TC-NCPA-01 |
| REQ-NCPA-02 | The deploy wizard checks host-key trust and login before starting | FMR, MAN NCPA | TC-NCPA-02, 03 |
| REQ-NCPA-03 | A live run banner, Deployment History, and a run drawer show progress and outcome | FMR | TC-NCPA-04 |
| REQ-NCPA-04 | Clean up applies to trusted failed and deployed devices and clears credential fields after each request | FMR (#182) | TC-NCPA-05, 06 |
| REQ-NCPA-05 | Credentials never appear in responses or history | QA J3-03 | TC-NCPA-07 |
| REQ-NCPA-06 | NCPA Deployment needs `system.deploy.ncpa` | FMR | TC-NCPA-08 |
| REQ-NCPA-07 | Remote restart settings save up to 20 services and need a trusted device and no running deployment | FMR (#182), MAN Remote\_Service\_Restart | TC-NCPA-09, 10 |
| REQ-NCPA-08 | Clean up warns that remote restarts stop until the device is deployed again | FMR (#182) | TC-NCPA-11 |
| REQ-MNT-01 | The list shows its states, including "No maintenance windows yet" | DR §6 | TC-MNT-01 |
| REQ-MNT-02 | Create and edit enforce: end after start, ends in the future, one-off at most 30 days, repeats not longer than their period, repeat end within 366 days, reason 1 to 200 characters | DR §6, MAN | TC-MNT-02, 03, 04, 05, 06 |
| REQ-MNT-03 | Cancel takes two clicks and removes pending and running downtime | DR §6 | TC-MNT-07 |
| REQ-MNT-04 | If Nagios cannot be told, the window still changes and a notice says so | DR §6 | TC-MNT-08 |
| REQ-MNT-05 | Paused, retired, and missing devices cannot be chosen, and the page needs `maintenance.manage` | DR §6, MAN | TC-MNT-09 |
| REQ-MNT-06 | An active window shows downtime on covered devices and silences their alerts | DR §6 | TC-MNT-10 |
| REQ-REM-01 | With only `remediation.view` the page is read-only | FMR | TC-REM-01 |
| REQ-REM-02 | Adding or editing an action validates and shows server messages against the right field | FMR | TC-REM-02 |
| REQ-REM-03 | Actions can be enabled, disabled, and deleted with confirmation | FMR | TC-REM-03 |
| REQ-REM-04 | Changes need `remediation.manage` | FMR | TC-REM-04 |
| REQ-REM-05 | A 409 offers a reload and a 422 shows the Nagios message | FMR | TC-REM-05 |
| REQ-REM-06 | The Run log filters, shows skip reasons, and a drawer with redacted output | FMR | TC-REM-06 |
| REQ-REM-07 | The kill switch stops all actions, shows its state, survives a reload, and logs covered failures as skipped | FMR (#155), MAN Automatic\_Recovery | TC-REM-07 |
| REQ-REM-08 | The status panel shows consumer health and a stalled warning | FMR (#155) | TC-REM-08 |
| REQ-REM-09 | Acknowledged problems are skipped unless Run when acknowledged is ticked | MAN Automatic\_Recovery | TC-REM-09 |
| REQ-REM-10 | The action form shows the right parameters per action type and clears them when the type changes | FMR (#182) | TC-REM-10 |

### Reports, logs, settings

| Req | Requirement | Source | Test cases |
| --- | --- | --- | --- |
| REQ-RPT-01 | Host Availability: one row per monitored host, uptime between 0 and 100 | QA J8-01 | TC-RPT-01 |
| REQ-RPT-02 | Network Services totals match System Status | QA J8-02 | TC-RPT-02 |
| REQ-RPT-03 | Export as CSV, Excel (`.xls`), and PDF print view with the same rows | QA J8-03 to J8-05 | TC-RPT-03, 04 |
| REQ-RPT-04 | Every export is logged with user, type, format, range, and time | QA J8-06 | TC-RPT-05 |
| REQ-RPT-05 | An empty period shows an empty state | QA J8-07 | TC-RPT-06 |
| REQ-RPT-06 | Reports need `system.report` | FMR | TC-RPT-07 |
| REQ-LOG-01 | Five audit log categories list entries, filter, export, and record actions | FMR, MAN | TC-LOG-01, 02 |
| REQ-LOG-02 | The Nagios log tab shows at most the latest 200 lines, newest last, with a refresh | MAN Storage | TC-LOG-03 |
| REQ-LOG-03 | Free-form Nagios log text is redacted and an unreadable log gives an unavailable message | MAN Storage | TC-LOG-04 |
| REQ-LOG-04 | System Logs need `system.logs` | FMR | TC-LOG-05 |
| REQ-SET-01 | Dashboard Refresh Rate offers Manual, 1, 5, 15 minutes per user | DR §3.1 | TC-SET-01 |
| REQ-SET-02 | Data polling interval offers 30, 60, 120, 300 seconds (default 60), and a save takes effect at once | DR §3.1 | TC-SET-02 |
| REQ-SET-03 | Check interval (1, 2, 5, 10, 15), Retry interval (1 to 10, not above Check), and Maximum attempts (1 to 10) follow their rules | DR §3.1 | TC-SET-03, 04 |
| REQ-SET-04 | Flap thresholds accept 0 to 100 or empty, and invalid values are explained and not sent | DR §3.1 | TC-SET-05 |
| REQ-SET-05 | The Notification Policy card validates times, order, and overlap, and handles stale saves | FMR | TC-SET-06 |
| REQ-SET-06 | Email settings validate the relay host and port, keep a stored password, and send a test email | FMR | TC-SET-07 |
| REQ-SET-07 | A failed save restores the old values, and Maintenance Mode pauses only Pinpoint's own jobs | DR §3.1, §6 | TC-SET-08, 09 |

### Discovery, device extras, shell, quality

| Req | Requirement | Source | Test cases |
| --- | --- | --- | --- |
| REQ-DSC-01 | A scan finds every target in the configured subnet and records IP, MAC, hostname, and OS | QA J2-01, J2-03 | TC-DSC-01 |
| REQ-DSC-02 | A scan shows progress and ends in exactly one of Success, Failed, Interrupted | QA J2-02 | TC-DSC-02 |
| REQ-DSC-03 | Cancel stops a running scan, ends it as Interrupted, and logs it | QA J2-06 | TC-DSC-03 |
| REQ-DSC-04 | A rescan with no change reports that Nagios was not reloaded | QA J2-05 | TC-DSC-04 |
| REQ-DSC-05 | Discovery settings apply to the next scan and the edit is logged | QA J2-09 | TC-DSC-05 |
| REQ-DSC-06 | Removing a network keeps device ownership and does not make scanned devices Address Unknown | DIR #35 | TC-DSC-06 |
| REQ-DSC-07 | A port that is no longer seen becomes Missing and is not deleted after one missed scan | DIR §4 | TC-DSC-07 |
| REQ-DSC-08 | Starting and cancelling a scan needs `system.discover` | QA J2-06 | TC-DSC-08 |
| REQ-DSC-09 | Rescan Network starts at once and is disabled while scanning (the journey plan expects a confirmation) | QA J2-02, app differs | TC-DSC-09 |
| REQ-DX-01 | Check options show only on Monitored or Missing http, https, pop3, imap, pop3s, imaps ports | DIR #24 | TC-DX-01 |
| REQ-DX-02 | Check options fields depend on the service, and invalid values (status codes outside 100 to 599, bad host or method) are blocked | DIR §5, #24 | TC-DX-02, 05 |
| REQ-DX-03 | Saved options persist, reload on reopen, and Reset to defaults removes them | DIR §5 | TC-DX-03 |
| REQ-DX-04 | Check options are read-only without `system.hosts.edit` or for a retired or merged device | DIR §5, #24 | TC-DX-04 |
| REQ-DX-05 | The SNMP section validates fields per version and level, shows saved passwords only as "Saved", and needs edit permission to change and Test | FMR | TC-DX-06 |
| REQ-DX-06 | The Interfaces section shows for SNMP devices only, with a Monitor checkbox and Refresh | FMR | TC-DX-07 |
| REQ-DX-07 | Email alert recipients need `system.hosts.alerts`, fall back to default recipients, label ineligible users, and keep the old selection on a failed apply | DIR §13 | TC-DX-08, 09, 10 |
| REQ-SHL-01 | A notification escalation can be created and is applied to Nagios | `Backend_Modules_and_Routes.md`, `Implementation_Status.md` | TC-SHL-01 |
| REQ-SHL-02 | An invalid escalation is refused (400) and a failed Nagios apply is rolled back (422) | `Backend_Modules_and_Routes.md` | TC-SHL-02 |
| REQ-SHL-03 | Deleting an escalation applies, and a failed apply restores the range | `Backend_Modules_and_Routes.md` | TC-SHL-03 |
| REQ-SHL-04 | The strong-password policy setting is enforced when passwords are set | `Data_Model_and_Integrations.md` | TC-SHL-04 |
| REQ-SHL-05 | The Appliance storage card shows sizes and free space, warns below 10% free, shows Unavailable, and needs the Dashboard permission | MAN Storage | TC-SHL-05, 06 |
| REQ-SHL-06 | The header bell shows an unread count that matches its panel | `Backend_Modules_and_Routes.md` | TC-SHL-07 |
| REQ-SHL-07 | The General, Show notification bell toggle only shows or hides the bell and does not stop email | FMR | TC-SHL-08 |
| REQ-SHL-08 | A pending forgot-password request shows in the administrator's bell and in Manage Accounts | `Backend_Modules_and_Routes.md` | TC-SHL-09 |
| REQ-SHL-09 | The sidebar shows only the pages the user may open | FMR | TC-SHL-10 |
| REQ-NFR-01 | Protected API routes need a valid session (401 without one) | `Backend_Modules_and_Routes.md` | TC-NFR-01, 02 |
| REQ-NFR-02 | Script and SQL characters in inputs are treated as plain text | `Engineering_Standards.md` | TC-NFR-03 |
| REQ-NFR-03 | Pages are usable in light and dark mode and at a narrow width | DIR #19 | TC-NFR-04, 05 |
| REQ-NFR-04 | Every section has loading, error with Retry, and empty states | DR §3.2, DIR #16 | TC-NFR-06 |
| REQ-NFR-05 | System initialization takes 10 seconds or less | QA PT-01 | TC-NFR-07 |
| REQ-NFR-06 | Availability for 10 hosts takes 5 seconds or less | QA PT-02 | TC-NFR-08 |
| REQ-NFR-07 | A Dashboard refresh with 15 updates takes 3 seconds or less | QA PT-03 | TC-NFR-09 |
| REQ-NFR-08 | An alert shows within 3 seconds of the Nagios state change | QA PT-04 | TC-NFR-10 |
| REQ-NFR-09 | The system stays stable over a 4-hour run | QA PT-05 | TC-NFR-11 |

### Edge cases and robustness

| Req | Requirement | Source | Test cases |
| --- | --- | --- | --- |
| REQ-EDG-01 | Very long text is accepted and shown without breaking the page, or refused with a message that names the limit | Test practice | TC-EDG-01 |
| REQ-EDG-02 | Accents, emoji, quotes, and symbols in names are saved, shown, searched, and exported as typed, as plain text | Test practice | TC-EDG-02 |
| REQ-EDG-03 | Blank and space-only values are refused | Test practice | TC-EDG-03 |
| REQ-EDG-04 | A double click on Save creates exactly one record | Test practice | TC-EDG-04 |
| REQ-EDG-05 | Back and refresh never show protected data after sign-out or leave half-done work behind | Test practice | TC-EDG-05 |
| REQ-EDG-06 | A lost connection during a save shows an error, keeps the entries, and does not duplicate on retry | Test practice | TC-EDG-06 |
| REQ-EDG-07 | A request made after the session ended is refused and creates nothing | Test practice, `Backend_Modules_and_Routes.md` | TC-EDG-07 |
| REQ-EDG-08 | Two people editing one role leave it in one consistent state and a lost update is reported | Test practice | TC-EDG-08 |
| REQ-EDG-09 | Repeating an action many times ends in the right state and logs each action | Test practice | TC-EDG-09 |
| REQ-EDG-10 | A time zone change moves every time on screen consistently | FMR | TC-EDG-10 |
| REQ-EDG-11 | A window across midnight is accepted, and a daily window keeps the same local time | MAN Maintenance windows | TC-EDG-11 |
| REQ-EDG-12 | Special characters and long text in search boxes cause no error and no script runs | Test practice, `Engineering_Standards.md` | TC-EDG-12 |
| REQ-EDG-13 | Password length limits are exact: 12 with the strong policy and 8 without it | FMR, `validation.py` rules | TC-EDG-13 |
| REQ-EDG-14 | An email in a different letter case counts as a duplicate | Test practice | TC-EDG-14 |
| REQ-EDG-15 | Discovery ports and ranges accept 1 to 65535 and refuse values outside it | FMR | TC-EDG-15 |
| REQ-EDG-16 | A page reload during a scan keeps showing the scan and starts no second one | QA J2-02 | TC-EDG-16 |
| REQ-EDG-17 | Pages stay usable with 100 hosts, 500 services, and 5,000 events | Test practice | TC-EDG-17 |
| REQ-EDG-18 | Only one scan runs at a time and a second start is refused | `Backend_Modules_and_Routes.md` | TC-EDG-18 |

### Order of events

| Req | Requirement | Source | Test cases |
| --- | --- | --- | --- |
| REQ-SEQ-01 | An acknowledgement is never left on a service that has already recovered | DR §4.9 | TC-SEQ-01 |
| REQ-SEQ-02 | State changes during the retries are listed in order, and only a hard failure sends a notification | AHR §3, MAN Notification\_Policy | TC-SEQ-02 |
| REQ-SEQ-03 | A window that starts while an alert is active silences it, and notifications resume when the window ends | DR §6, MAN | TC-SEQ-03 |
| REQ-SEQ-04 | A window cancelled before it starts never silences anything | DR §6, MAN | TC-SEQ-04 |
| REQ-SEQ-05 | Editing a running window moves its end and removes the old downtime | MAN Maintenance windows | TC-SEQ-05 |
| REQ-SEQ-06 | A device paused during an alert shows its current state when resumed, with no stale alert | DIR §12 | TC-SEQ-06 |
| REQ-SEQ-07 | A pause made during a scan is kept after the scan | DIR §12.3 | TC-SEQ-07 |
| REQ-SEQ-08 | Discovery settings cannot be saved while a scan runs and can be saved after | FMR | TC-SEQ-08 |
| REQ-SEQ-09 | Enabling a plugin before the first scan gives the same result as enabling it after | DIR §4 | TC-SEQ-09 |
| REQ-SEQ-10 | Disabling a plugin stops its services and explains the port, and enabling it brings them back | DIR §4 | TC-SEQ-10 |
| REQ-SEQ-11 | A scan does not turn a stopped port back into Monitored | DIR §5 | TC-SEQ-11 |
| REQ-SEQ-12 | Deactivating a role removes its permissions from signed-in users at once | `Implementation_Status.md`, FMR | TC-SEQ-12 |
| REQ-SEQ-13 | A permission removed from a role stops working on the user's next request | FMR | TC-SEQ-13 |
| REQ-SEQ-14 | A suspended user is signed out and cannot sign in | QA J9-05 | TC-SEQ-14 |
| REQ-SEQ-15 | A password reset ends the user's open session | QA J9-07 | TC-SEQ-15 |
| REQ-SEQ-16 | A forced password change shows at every sign-in until it is done | FMR | TC-SEQ-16 |
| REQ-SEQ-17 | An interrupted first-run setup shows again and blocks everything else | QA J1-07 | TC-SEQ-17 |
| REQ-SEQ-18 | A failure that arrives while the kill switch is off is logged as skipped and is not run later | MAN Automatic\_Recovery | TC-SEQ-18 |
| REQ-SEQ-19 | Cooldown and the hourly limit skip runs in the right order | MAN Automatic\_Recovery | TC-SEQ-19 |
| REQ-SEQ-20 | Maintenance Mode and scheduled downtime skip actions with their own reasons | MAN Automatic\_Recovery | TC-SEQ-20 |
| REQ-SEQ-21 | Disabling `check_ncpa` stops NCPA monitoring and enabling it restores it without redeploying | FMR | TC-SEQ-21 |
| REQ-SEQ-22 | After Clean up remote restarts stop until the device is redeployed | MAN Remote\_Service\_Restart | TC-SEQ-22 |
| REQ-SEQ-23 | Every page shows the same event order | AHR §5.4 | TC-SEQ-23 |
| REQ-SEQ-24 | A scan interrupted by a restart ends with a final status and a new scan can start | QA J2-02 | TC-SEQ-24 |
